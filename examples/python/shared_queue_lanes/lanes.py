"""Deterministic one-worker scheduler for a queue shared by people and agents.

Author: Sandeep Belgavi. Synthetic fixtures only; this is a teaching model, not a queue product.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    id: str
    source: str      # 'human' or 'agent'
    arrival: int     # tick at which the item becomes visible
    priority: int    # larger is more urgent


POLICIES = ('strict', 'aging', 'lanes')


def _pick(ready, policy, tick, aging, weights, credit):
    if policy == 'strict':
        return min(ready, key=lambda i: (-i.priority, i.arrival, i.id))
    if policy == 'aging':
        return min(ready, key=lambda i: (-(i.priority + aging * (tick - i.arrival)), i.arrival, i.id))
    # lanes: weighted round robin between sources, FIFO inside a lane.
    by_lane = {}
    for item in ready:
        by_lane.setdefault(item.source, []).append(item)
    lanes = sorted(by_lane)
    if all(credit.get(lane, 0) <= 0 for lane in lanes):
        for lane in weights:
            credit[lane] = weights[lane]
    lane = max(lanes, key=lambda name: (credit.get(name, 0), name == 'human'))
    credit[lane] = credit.get(lane, 0) - 1
    return min(by_lane[lane], key=lambda i: (i.arrival, i.id))


def simulate(items, policy, ticks, aging=0, weights=None):
    """Run one item per tick. Return (start tick per id or None, decision trace)."""
    if policy not in POLICIES:
        raise ValueError(f'unknown policy {policy!r}')
    if ticks < 0 or aging < 0:
        raise ValueError('ticks and aging must be non-negative')
    weights = dict(weights or {'human': 1, 'agent': 1})
    if any(w <= 0 for w in weights.values()):
        raise ValueError('lane weights must be positive')
    pending = sorted(items, key=lambda i: (i.arrival, i.id))
    started = {i.id: None for i in items}
    credit, trace = {}, []
    for tick in range(ticks):
        ready = [i for i in pending if i.arrival <= tick]
        if not ready:
            trace.append((tick, None, 'idle'))
            continue
        chosen = _pick(ready, policy, tick, aging, weights, credit)
        pending.remove(chosen)
        started[chosen.id] = tick
        trace.append((tick, chosen.id, chosen.source))
    return started, trace


def flood_fixture(agent_per_tick=2, ticks=20):
    """One human help-desk case CASE-1001 at tick 0 behind a sustained agent stream."""
    items = [Item('CASE-1001', 'human', 0, 3)]
    for tick in range(ticks):
        for k in range(agent_per_tick):
            items.append(Item(f'AGENT-{tick:02d}-{k}', 'agent', tick, 5))
    return items
