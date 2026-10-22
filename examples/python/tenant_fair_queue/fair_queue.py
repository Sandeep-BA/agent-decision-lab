"""Admission control for a shared internal service that agent tenants call.

Author: Sandeep Belgavi. Companion to "Agent Traffic on Shared Internal Services" (aicassindra.com).

Three pieces, each usable on its own:

* ``FifoAdmission``  - one bounded queue for everybody (the usual starting point).
* ``FairAdmission``  - one bounded queue per tenant, served round-robin, so a tenant can only
  fill and wait in its own queue.
* ``AgentBudget``    - a token bucket that the agent runtime checks before it sends a call,
  plus a limit on re-plan rounds, so failures cannot multiply the agent's own traffic.

``simulate`` runs a small deterministic scenario on a 10 ms clock: three ordinary tenants and
one agent tenant whose loop speeds up for a while and re-plans every refused or abandoned call.
Nothing here calls a model or a network service.
"""
from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import dataclass, field

TICK_MS = 10


@dataclass
class Call:
    tenant: str
    arrived: int          # tick
    round: int = 0        # 0 for an original call, n for the n-th re-plan round


class FifoAdmission:
    """One bounded FIFO queue shared by every tenant."""

    def __init__(self, limit: int):
        self.limit, self.queue = limit, deque()

    def offer(self, call: Call) -> bool:
        if len(self.queue) >= self.limit:
            return False
        self.queue.append(call)
        return True

    def expire(self, now: int, max_wait: int) -> list[Call]:
        gone = [c for c in self.queue if now - c.arrived >= max_wait]
        self.queue = deque(c for c in self.queue if now - c.arrived < max_wait)
        return gone

    def take(self) -> Call | None:
        return self.queue.popleft() if self.queue else None

    def __len__(self) -> int:
        return len(self.queue)


class FairAdmission:
    """One bounded queue per tenant, dispatched round-robin (deficit round robin with equal quanta)."""

    def __init__(self, tenants: list[str], limit_per_tenant: int):
        self.order = list(tenants)
        self.limit = limit_per_tenant
        self.queues = {t: deque() for t in tenants}
        self.next = 0

    def offer(self, call: Call) -> bool:
        q = self.queues[call.tenant]
        if len(q) >= self.limit:
            return False
        q.append(call)
        return True

    def expire(self, now: int, max_wait: int) -> list[Call]:
        gone = []
        for t, q in self.queues.items():
            gone += [c for c in q if now - c.arrived >= max_wait]
            self.queues[t] = deque(c for c in q if now - c.arrived < max_wait)
        return gone

    def take(self) -> Call | None:
        for _ in range(len(self.order)):
            t = self.order[self.next % len(self.order)]
            self.next += 1
            if self.queues[t]:
                return self.queues[t].popleft()
        return None

    def __len__(self) -> int:
        return sum(len(q) for q in self.queues.values())


@dataclass
class AgentBudget:
    """Token bucket checked by the agent runtime before each call, and a cap on re-plan rounds."""
    per_second: float           # 0 disables the bucket
    max_rounds: int = 3
    tokens: float = field(default=0.0)

    def __post_init__(self):
        self.tokens = self.per_second

    def refill(self) -> None:
        if self.per_second:
            self.tokens = min(self.per_second, self.tokens + self.per_second * TICK_MS / 1000)

    def allow(self, call: Call) -> bool:
        if call.round > self.max_rounds:
            return False
        if not self.per_second:
            return True
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


def simulate(policy: str = "fifo", workers: int = 8, service_ms: int = 200, normal_rate: int = 8,
             agent_rate: int = 8, runaway_rate: int = 40, runaway=(30, 70), replan: int = 2,
             queue_limit: int = 200, max_wait_ms: int = 2000, budget: float = 0, seconds: int = 120) -> dict:
    tenants = ["A", "B", "C", "D"]
    adm = FairAdmission(tenants, queue_limit // 4) if policy == "fair" else FifoAdmission(queue_limit)
    agent = AgentBudget(budget)
    stats = {t: dict(offered=0, served=0, refused=0, abandoned=0, replans=0, held=0) for t in tenants}
    running: list[int] = []
    pending: list[tuple[int, int]] = []          # (due tick, round) for agent re-plans
    nxt = {"A": 0.0, "B": 1000 / normal_rate / 3, "C": 2000 / normal_rate / 3}
    acc_d = 0.5
    svc, max_wait = service_ms // TICK_MS, max_wait_ms // TICK_MS

    def failed(call: Call, kind: str, now: int) -> None:
        stats[call.tenant][kind] += 1
        if call.tenant == "D" and call.round < agent.max_rounds:
            for _ in range(replan):
                pending.append((now + 50, call.round + 1))   # the agent re-plans 0.5 s later
                stats["D"]["replans"] += 1

    for now in range(seconds * 1000 // TICK_MS):
        t0, t1 = now * TICK_MS, (now + 1) * TICK_MS
        running = [done for done in running if done > now]
        arrivals = []
        for t in "ABC":
            while nxt[t] < t1:
                arrivals.append((nxt[t], Call(t, now)))
                nxt[t] += 1000 / normal_rate
        rate = runaway_rate if runaway[0] * 1000 <= t0 < runaway[1] * 1000 else agent_rate
        acc_d += rate * TICK_MS / 1000
        n_d = int(acc_d + 1e-9)
        acc_d -= n_d
        arrivals += [(t0 + (k + 0.5) * TICK_MS / n_d, Call("D", now)) for k in range(n_d)]
        due = [r for d, r in pending if d == now]
        pending = [(d, r) for d, r in pending if d != now]
        arrivals += [(t0, Call("D", now, r)) for r in due]
        arrivals.sort(key=lambda a: a[0])
        agent.refill()
        for _, call in arrivals:
            if call.tenant == "D" and not agent.allow(call):
                stats["D"]["held"] += 1
                continue
            stats[call.tenant]["offered"] += 1
            if not adm.offer(call):
                failed(call, "refused", now)
        for call in adm.expire(now, max_wait):
            failed(call, "abandoned", now)
        while len(running) < workers:
            call = adm.take()
            if call is None:
                break
            stats[call.tenant]["served"] += 1
            running.append(now + svc)
    ordinary = [stats[t] for t in "ABC"]
    pct = lambda s: round(100 * s["served"] / s["offered"], 1) if s["offered"] else 100.0
    return dict(policy=policy, budget=budget, tenants=stats,
                ordinary_served_pct=round(100 * sum(s["served"] for s in ordinary) / sum(s["offered"] for s in ordinary), 1),
                worst_ordinary_pct=min(pct(s) for s in ordinary))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--policy", choices=["fifo", "fair"], default="fifo")
    ap.add_argument("--budget", type=float, default=0, help="agent calls per second, 0 = no budget")
    ap.add_argument("--replan", type=int, default=2)
    args = ap.parse_args()
    print(json.dumps(simulate(args.policy, replan=args.replan, budget=args.budget), indent=2))


if __name__ == "__main__":
    main()
