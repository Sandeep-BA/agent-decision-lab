"""Author: Sandeep Belgavi. Compare head sampling with outcome-based tail sampling for synthetic agent runs.

Each run of a fictional Belgavi's Book Store help-desk agent is split into trace segments at durable
pauses (a human approval wait). The script compares three policies on the same 20,000 runs:

  head     - keep each segment trace with probability 5 percent, decided at its first span
  tail     - keep a segment if it errored, wrote something, or belongs to a run that asked for approval
             (a run-level flag carried on every segment); otherwise keep it when the run-level sample
             bucket, derived from the run id and carried on every segment, is below 5
  tail-tid - the same rules, but routine segments are sampled by hashing their own trace id
  tail+pause - the tail rules plus: always keep a segment that ends in a durable pause

No collector, exporter or model is involved; the rules mirror policy types documented for the
OpenTelemetry Collector tail sampling processor (status_code, numeric_attribute, boolean_attribute,
probabilistic) so the decisions can be reasoned about offline.
"""
import hashlib
import json
import random

RUNS = 20_000
ARRIVALS_PER_SECOND = 3.0
DECISION_WAIT_S = 30
SAMPLE_PERCENT = 5


def bucket(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big") % 100


def make_runs(seed: int = 26):
    rnd = random.Random(seed)
    runs = []
    for i in range(RUNS):
        run_id = f"CASE-{10000 + i}"
        approval = rnd.random() < 0.10
        direct_write = (not approval) and rnd.random() < 0.12
        waits_for_reply = (not approval) and rnd.random() < 0.15
        error = rnd.random() < 0.03
        flags = {"approval_in_run": approval}
        first = {"trace_id": run_id + "-s1", "seconds": rnd.randint(4, 40), "error": False,
                 "writes": 1 if direct_write else 0, **flags}
        segments = [first]
        if approval or waits_for_reply:
            first["ends_in_pause"] = True
            approved = approval and rnd.random() < 0.8
            segments.append({"trace_id": run_id + "-s2", "seconds": rnd.randint(5, 20), "error": False,
                             "writes": 1 if approved else 0, **flags,
                             "pause_before_s": rnd.randint(120, 1800) if approval else rnd.randint(600, 7200)})
        if error:
            rnd.choice(segments)["error"] = True
        runs.append({"run_id": run_id, "segments": segments,
                     "important": approval or direct_write or error})
    return runs


def keep(policy: str, run: dict, seg: dict) -> bool:
    if policy == "head":
        return bucket("head:" + seg["trace_id"]) < SAMPLE_PERCENT
    if seg["error"] or seg["writes"] > 0 or seg["approval_in_run"]:
        return True
    if policy == "tail+pause" and seg.get("ends_in_pause"):
        return True
    key = seg["trace_id"] if policy == "tail-tid" else run["run_id"]
    return bucket("tail:" + key) < SAMPLE_PERCENT


def evaluate(policy: str, runs):
    kept = total = 0
    signal_total = signal_kept = 0
    approval_runs = approval_complete = 0
    routine_multi = routine_partial = 0
    lost_context = 0
    for run in runs:
        segs = run["segments"]
        decisions = [keep(policy, run, s) for s in segs]
        total += len(segs)
        kept += sum(decisions)
        for i, (seg, d) in enumerate(zip(segs, decisions)):
            if seg["error"] or seg["writes"]:
                signal_total += 1
                signal_kept += d
                if d and not all(decisions[:i]):
                    lost_context += 1
        if segs[0]["approval_in_run"]:
            approval_runs += 1
            approval_complete += all(decisions)
        if len(segs) > 1 and not any(s["error"] or s["writes"] or s["approval_in_run"] for s in segs):
            routine_multi += 1
            routine_partial += any(decisions) and not all(decisions)
    return {"policy": policy, "segments": total, "kept_segments": kept,
            "kept_percent": round(100 * kept / total, 1),
            "error_or_write_segments": signal_total, "error_or_write_segments_kept": signal_kept,
            "approval_runs": approval_runs, "approval_runs_complete": approval_complete,
            "routine_multi_segment_runs": routine_multi, "routine_runs_kept_partially": routine_partial,
            "kept_error_or_write_segments_missing_an_earlier_segment": lost_context}


def single_trace_split(runs, decision_wait_s: int = DECISION_WAIT_S):
    """If a whole run were one trace, how many runs outlast the decision wait?"""
    long_runs = sum(1 for r in runs if sum(s["seconds"] + s.get("pause_before_s", 0) for s in r["segments"]) > decision_wait_s)
    return long_runs


def memory_traces(runs, decision_wait_s: int) -> int:
    segments_per_run = sum(len(r["segments"]) for r in runs) / len(runs)
    return round(ARRIVALS_PER_SECOND * segments_per_run * decision_wait_s)


def main():
    runs = make_runs()
    out = {"runs": len(runs),
           "results": [evaluate(p, runs) for p in ("head", "tail", "tail-tid", "tail+pause")],
           "runs_longer_than_decision_wait_if_one_trace": single_trace_split(runs),
           "traces_in_memory_at_decision_wait_30s": memory_traces(runs, 30),
           "traces_in_memory_if_decision_wait_covered_1800s_pauses": memory_traces(runs, 1800)}
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
