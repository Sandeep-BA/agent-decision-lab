# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

"""One deadline through a five-hop agent run: fixed per-hop timeouts versus a propagated budget.

The hops and defaults match the lab at aicassindra.com/labs/system_design/agent_run_deadline_budget.html
Times are integer milliseconds and the clock is simulated, so results are exact and nothing sleeps.
"""
import json
import sys


class BudgetExhausted(Exception):
    """Too little time is left to start this hop usefully."""


class Deadline:
    def __init__(self, seconds, clock):
        self._clock = clock
        self._at = clock() + seconds

    def remaining(self):
        return self._at - self._clock()

    def for_hop(self, cap, reserve=0.0, min_useful=0.5):
        left = self.remaining() - reserve
        if left < min_useful:
            raise BudgetExhausted(f"{left:.3f}s left, {min_useful}s needed")
        return min(cap, left)


def run(policy="fixed", deadline_ms=20000, model_ms=3000, lookup_ms=400, refund_ms=16000,
        model_timeout=15000, tool_timeout=10000, tool_retries=1, reserve=3000, min_useful=2000,
        cancel=False, idempotent=False):
    """Walk the five hops and return the outcome. `cancel` means a client timeout stops the server."""
    now = [0]
    deadline = Deadline(deadline_ms, lambda: now[0])
    hops = [("model", model_ms, False), ("tool", lookup_ms, False), ("model", model_ms, False),
            ("tool", refund_ms, True), ("model", model_ms, False)]
    ghost = refunds = retries = skipped = 0
    fallback = False
    reply_at = None
    for index, (kind, latency, is_refund) in enumerate(hops):
        last = index == len(hops) - 1
        cap = model_timeout if kind == "model" else tool_timeout
        attempts = tool_retries + 1 if kind == "tool" else 1
        done = False
        for attempt in range(attempts):
            if policy == "propagate":
                try:
                    timeout = deadline.for_hop(cap, 0 if last else reserve, min_useful)
                except BudgetExhausted:
                    skipped += 1
                    break
            else:
                timeout = cap
            if latency <= timeout:
                now[0] += latency
                done = True
                if is_refund:
                    refunds += 1
                if last:
                    reply_at = now[0]
                break
            now[0] += timeout
            if attempt > 0:
                retries += 1
            if not cancel:
                ghost += latency - timeout
                if is_refund and (not idempotent or refunds == 0):
                    refunds += 1
        if last and not done and policy == "propagate":
            fallback = True
            reply_at = min(now[0], deadline_ms)
    delivered = reply_at is not None and reply_at <= deadline_ms
    return dict(finished=now[0], overrun=max(0, now[0] - deadline_ms), ghost=ghost, refunds=refunds,
                retries=retries, skipped=skipped, delivered=delivered, fallback=fallback)


if __name__ == "__main__":
    for policy in ("fixed", "propagate"):
        print(policy, json.dumps(run(policy=policy)))
    sys.exit(0)
