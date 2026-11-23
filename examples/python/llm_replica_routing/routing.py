"""Seeded simulation of routing LLM requests across replicas. Author: Sandeep Belgavi.

This is a simulation with assumed constants, not a measurement of any serving
engine. Each replica is a simplified continuous-batching server:

- at most MAX_RUNNING requests decode together; each decode step produces one
  token for every running request and takes STEP_BASE + STEP_PER_SEQ * running
  seconds (assumed constants);
- a request is admitted only when its KV reservation (prompt + max_tokens) fits
  in KV_TOKENS, otherwise it waits in a FIFO queue on that replica (real engines
  allocate KV blocks incrementally and may preempt; reserving the cap up front
  is a deliberate simplification);
- 90 % of requests are short (500-token prompt, max_tokens 300) and 10 % long
  (2,000-token prompt, max_tokens 4,000); the true output length is uniform
  between half the cap and the cap, and the router never sees it.

Routers compared, with the signal each one needs:
- round_robin: none;
- least_requests: requests running + waiting per replica;
- p2c_requests: the same count for two randomly chosen replicas;
- least_kv: reserved KV tokens (running + waiting) per replica.

Standard library only.
"""
from __future__ import annotations

import json
import random

REPLICAS = 4
MAX_RUNNING = 16
KV_TOKENS = 24_000
STEP_BASE = 0.010
STEP_PER_SEQ = 0.0005
DT = 0.01
ROUTERS = ('round_robin', 'least_requests', 'p2c_requests', 'least_kv')


def make_requests(seed: int, n: int, rate: float, long_share: float = 0.10) -> list[dict]:
    rng = random.Random(seed)
    t, out = 0.0, []
    for i in range(n):
        t += rng.expovariate(rate)
        long = rng.random() < long_share
        prompt, cap = (2000, 4000) if long else (500, 300)
        out.append({'id': i, 'arrive': t, 'prompt': prompt, 'cap': cap,
                    'tokens': rng.randint(cap // 2, cap), 'long': long})
    return out


def _reserved(req: dict) -> int:
    return req['prompt'] + req['cap']


def simulate(requests: list[dict], router: str, seed: int = 7) -> dict:
    if router not in ROUTERS:
        raise ValueError(f'unknown router {router}')
    rng = random.Random(seed)
    running = [[] for _ in range(REPLICAS)]   # [request, tokens generated]
    waiting = [[] for _ in range(REPLICAS)]
    done, rr, t, i = [], 0, 0.0, 0
    pending = sorted(requests, key=lambda r: r['arrive'])
    peak_wait = 0

    def load(r):
        return len(running[r]) + len(waiting[r])

    def kv(r):
        return sum(_reserved(x[0]) for x in running[r]) + sum(_reserved(x) for x in waiting[r])

    while i < len(pending) or any(running) or any(waiting):
        while i < len(pending) and pending[i]['arrive'] <= t:
            req = pending[i]; i += 1
            if router == 'round_robin':
                k = rr % REPLICAS; rr += 1
            elif router == 'least_requests':
                k = min(range(REPLICAS), key=lambda r: (load(r), r))
            elif router == 'p2c_requests':
                a, b = rng.sample(range(REPLICAS), 2)
                k = a if load(a) <= load(b) else b
            else:
                k = min(range(REPLICAS), key=lambda r: (kv(r), r))
            req['replica'] = k
            waiting[k].append(req)
        for r in range(REPLICAS):
            used = sum(_reserved(x[0]) for x in running[r])
            while waiting[r] and len(running[r]) < MAX_RUNNING and used + _reserved(waiting[r][0]) <= KV_TOKENS:
                req = waiting[r].pop(0)
                req['started'] = t
                running[r].append([req, 0.0])
                used += _reserved(req)
            peak_wait = max(peak_wait, len(waiting[r]))
            if not running[r]:
                continue
            gain = DT / (STEP_BASE + STEP_PER_SEQ * len(running[r]))
            still = []
            for item in running[r]:
                item[1] += gain
                if item[1] >= item[0]['tokens']:
                    done.append((item[0], t + DT))
                else:
                    still.append(item)
            running[r] = still
        t += DT

    def pct(xs, p):
        xs = sorted(xs)
        return round(xs[min(len(xs) - 1, int(p / 100 * len(xs)))], 2)
    short_total = [end - q['arrive'] for q, end in done if not q['long']]
    short_queue = [q['started'] - q['arrive'] for q, _ in done if not q['long']]
    long_total = [end - q['arrive'] for q, end in done if q['long']]
    return {'router': router, 'completed': len(done),
            'short_p50_s': pct(short_total, 50), 'short_p95_s': pct(short_total, 95), 'short_p99_s': pct(short_total, 99),
            'short_queue_p99_s': pct(short_queue, 99), 'long_p50_s': pct(long_total, 50),
            'peak_waiting_on_one_replica': peak_wait,
            'long_requests_per_replica': [sum(1 for q, _ in done if q['replica'] == r and q['long']) for r in range(REPLICAS)]}


def run(seed: int = 3, n: int = 1200, rate: float = 3.0) -> list[dict]:
    reqs = make_requests(seed, n, rate)
    return [simulate([dict(r) for r in reqs], name) for name in ROUTERS]


if __name__ == '__main__':
    for row in run():
        print(json.dumps(row))
