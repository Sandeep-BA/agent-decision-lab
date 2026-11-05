"""Replay Pod outcomes against a Kubernetes Job spec: backoffLimit, podFailurePolicy rules and disruptions.

Author: Sandeep Belgavi. Original example for the aicassindra.com article "Kubernetes Jobs That Retry the Wrong
Failures: backoffLimit and podFailurePolicy". A model of the documented rules (Jobs docs and the Job v1 API
reference), not a client of a cluster. Standard library only.
Run: python jobpolicy.py fixtures/nights.json

Rules modelled: restartPolicy Never; podFailurePolicy rules evaluated in order, first match wins; FailJob fails
the Job at once; Ignore does not count and replaces the Pod; Count, or no matching rule, increments the failure
count; the Job fails when counted failures exceed backoffLimit (the number of retries). A rule matches on exit
codes (In / NotIn, value 0 not allowed with In) or on Pod condition type and status, never both. Back-off before
a replacement: 10 s doubling, capped at 600 s, after counted failures only (a simplification). activeDeadlineSeconds
fails the Job when reached.
"""
import json
import sys

OUTCOMES = {
    "ok": {"code": 0, "conditions": []},
    "exit1": {"code": 1, "conditions": []},
    "exit3": {"code": 3, "conditions": []},
    "oom": {"code": 137, "conditions": []},
    "evict": {"code": 143, "conditions": [{"type": "DisruptionTarget", "status": "True", "reason": "EvictionByEvictionAPI"}]},
    "pressure": {"code": 143, "conditions": [{"type": "DisruptionTarget", "status": "True", "reason": "TerminationByKubelet"}]},
}


def validate(policy):
    rules = policy.get("rules", [])
    if len(rules) > 20:
        raise ValueError("at most 20 rules are allowed")
    for r in rules:
        if r["action"] not in ("FailJob", "Ignore", "Count", "FailIndex"):
            raise ValueError("unknown action " + r["action"])
        if ("onExitCodes" in r) == ("onPodConditions" in r):
            raise ValueError("a rule needs exactly one of onExitCodes and onPodConditions")
        ec = r.get("onExitCodes")
        if ec and ec["operator"] == "In" and 0 in ec["values"]:
            raise ValueError("value 0 cannot be used for the In operator")


def rule_matches(rule, outcome):
    if "onExitCodes" in rule:
        ec = rule["onExitCodes"]
        inside = outcome["code"] in ec["values"]
        return outcome["code"] != 0 and (inside if ec["operator"] == "In" else not inside)
    return any(c["type"] == p["type"] and c["status"] == p.get("status", "True")
               for p in rule["onPodConditions"] for c in outcome["conditions"])


def replay(spec, outcomes, run_s=120, max_pods=100):
    policy = spec.get("podFailurePolicy", {"rules": []})
    validate(policy)
    limit, deadline = spec.get("backoffLimit", 6), spec.get("activeDeadlineSeconds")
    t = counted = pods = backoff = 0
    log = []
    while pods < max_pods:
        name = outcomes[min(pods, len(outcomes) - 1)]
        o = OUTCOMES[name]
        pods += 1
        dur = run_s // 2 if o["conditions"] else run_s
        if deadline and t + dur > deadline:
            return dict(result="failed", reason="DeadlineExceeded", pods=pods, counted=counted, t=deadline, backoff=backoff, log=log)
        t += dur
        if o["code"] == 0:
            log.append((pods, name, "-"))
            return dict(result="succeeded", reason="Pod succeeded", pods=pods, counted=counted, t=t, backoff=backoff, log=log)
        action = next((r["action"] for r in policy["rules"] if rule_matches(r, o)), "Count")
        log.append((pods, name, action))
        if action == "FailJob":
            return dict(result="failed", reason="FailJob rule", pods=pods, counted=counted, t=t, backoff=backoff, log=log)
        if action == "Ignore":
            if deadline and t >= deadline:
                return dict(result="failed", reason="DeadlineExceeded", pods=pods, counted=counted, t=deadline, backoff=backoff, log=log)
            continue
        counted += 1
        if counted > limit:
            return dict(result="failed", reason="BackoffLimitExceeded", pods=pods, counted=counted, t=t, backoff=backoff, log=log)
        delay = min(10 * 2 ** (counted - 1), 600)
        if deadline and t + delay >= deadline:
            return dict(result="failed", reason="DeadlineExceeded", pods=pods, counted=counted, t=deadline, backoff=backoff + deadline - t, log=log)
        t += delay
        backoff += delay
    return dict(result="active", reason="model stopped after %d Pods" % max_pods, pods=pods, counted=counted, t=t, backoff=backoff, log=log)


ARTICLE_POLICY = {"rules": [
    {"action": "FailJob", "onExitCodes": {"containerName": "importer", "operator": "In", "values": [3]}},
    {"action": "Ignore", "onPodConditions": [{"type": "DisruptionTarget"}]},
]}


def run(fixture):
    out = []
    for case in fixture["cases"]:
        spec = dict(case["spec"])
        if spec.pop("articlePolicy", False):
            spec["podFailurePolicy"] = ARTICLE_POLICY
        r = replay(spec, case["outcomes"])
        out.append({"name": case["name"], **{k: r[k] for k in ("result", "reason", "pods", "counted", "t", "backoff")}})
    return out


if __name__ == "__main__":
    with open(sys.argv[1] if len(sys.argv) > 1 else "fixtures/nights.json", encoding="utf-8") as f:
        print(json.dumps(run(json.load(f)), indent=2))
