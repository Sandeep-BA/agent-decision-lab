"""Commit tokens in tool results: an agent that verifies its own write against a lagging replica.

Author: Sandeep Belgavi. Companion to "When an Agent Checks Its Own Write: Replica Lag, Commit Tokens in
Tool Results and Duplicate Actions From Stale Verification" (aicassindra.com, System design).

A primary store appends every committed write to a log; a replica applies the log after a fixed lag.
A scripted agent (no model is called) issues a refund, reads the order back to verify it, and issues the
refund again if the read shows none. Three independent guards are compared:
  - the read tool honours a commit token returned by the write tool,
  - the read tool reports freshness so "not visible yet" differs from "none",
  - the refund carries an intent key derived from the case and the order.
Time is simulated in seconds; nothing sleeps and nothing touches a network.
"""
import json
import sys
from dataclasses import dataclass, field


@dataclass
class Store:
    """A primary with a commit log and a replica that applies the log `lag` seconds late."""
    lag: float
    log: list = field(default_factory=list)          # (commit_time, lsn, key, value)
    refunds: dict = field(default_factory=dict)      # intent key -> refund id (enforced on the primary)
    refund_count: int = 0

    def write(self, now, key, value):
        lsn = len(self.log) + 1
        self.log.append((now, lsn, key, value))
        return lsn

    def primary_get(self, key):
        val = None
        for _, _, k, v in self.log:
            if k == key:
                val = v
        return val, len(self.log)

    def replica_lsn(self, now):
        return max([lsn for t, lsn, _, _ in self.log if t + self.lag <= now], default=0)

    def replica_get(self, now, key):
        applied = self.replica_lsn(now)
        val = None
        for _, lsn, k, v in self.log:
            if k == key and lsn <= applied:
                val = v
        return val, applied


class Tools:
    def __init__(self, store, use_tokens, report_freshness, intent_keys, wait_s=0.5):
        self.s, self.use_tokens, self.report_freshness, self.intent_keys, self.wait_s = (
            store, use_tokens, report_freshness, intent_keys, wait_s)

    def issue_refund(self, now, case_id, order_id, attempt):
        key = f"{case_id}:{order_id}" if self.intent_keys else f"{case_id}:{order_id}:{attempt}"
        if key in self.s.refunds:
            return {"status": "ok", "duplicate": True, "refund_id": self.s.refunds[key],
                    "commit_token": None}
        self.s.refund_count += 1
        self.s.refunds[key] = f"R{self.s.refund_count}"
        lsn = self.s.write(now, f"order:{order_id}:refund", self.s.refunds[key])
        return {"status": "ok", "refund_id": self.s.refunds[key],
                "commit_token": lsn if self.use_tokens else None}

    def get_order(self, now, order_id, min_lsn=None):
        key = f"order:{order_id}:refund"
        waited = 0.0
        if min_lsn is not None:
            # Wait up to wait_s for the replica, then fall back to the primary.
            while self.s.replica_lsn(now + waited) < min_lsn and waited < self.wait_s:
                waited = round(waited + 0.05, 2)
            if self.s.replica_lsn(now + waited) < min_lsn:
                val, pos = self.s.primary_get(key)
                return {"refund": val or "none", "served_by": "primary", "waited_s": waited, "fresh": True}
        val, pos = self.s.replica_get(now + waited, key)
        result = {"refund": val or "none", "served_by": "replica", "waited_s": waited}
        if self.report_freshness:
            behind = len(self.s.log) - pos
            result["fresh"] = behind == 0
            if behind and val is None:
                result["refund"] = "unknown"
        return result


def run_agent(lag, use_tokens=False, report_freshness=False, intent_keys=False):
    """The scripted agent: refund, verify, and refund again only if the read clearly says none."""
    store = Store(lag=lag)
    tools = Tools(store, use_tokens, report_freshness, intent_keys)
    trace, now, token = [], 0.0, None
    r = tools.issue_refund(now, "CASE-4182", "BK-7731", attempt=1)
    token = r["commit_token"]
    trace.append(("issue_refund", now, r))
    now += 0.35
    read = tools.get_order(now, "BK-7731", min_lsn=token)
    trace.append(("get_order", now, read))
    if read["refund"] == "none":
        now += 0.75
        r2 = tools.issue_refund(now, "CASE-4182", "BK-7731", attempt=2)
        trace.append(("issue_refund", now, r2))
    return {"refunds_issued": store.refund_count,
            "agent_believed_first_failed": read["refund"] == "none",
            "verification_read": read, "trace": trace}


SCENARIOS = {
    "no_guards": {},
    "commit_token": {"use_tokens": True},
    "freshness_flag": {"report_freshness": True},
    "intent_key": {"intent_keys": True},
    "all_guards": {"use_tokens": True, "report_freshness": True, "intent_keys": True},
}


def main(lag):
    for name, opts in SCENARIOS.items():
        out = run_agent(lag, **opts)
        print(json.dumps({"scenario": name, "replica_lag_s": lag,
                          "refunds_issued": out["refunds_issued"],
                          "agent_believed_first_failed": out["agent_believed_first_failed"],
                          "verification_read": out["verification_read"]}))


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 2.1)
