"""Loop guards for agents subscribed to change events they can cause.

Author: Sandeep Belgavi. Companion to "Agents That React to Changes They Caused" (aicassindra.com).
Synthetic fixtures only: the agents are scripted functions, the store is a dict, nothing calls a model.

Guards: origin filter (ignore events you caused), no-op suppression (a write that changes nothing
publishes nothing), hop limit (causal depth from the human edit) and a per-product write cap.
"""
from collections import deque
from dataclasses import dataclass, field
import hashlib
import json


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


@dataclass
class Event:
    id: int
    product: str
    field: str
    origin: str
    causation: int | None
    hop: int


@dataclass
class Guards:
    origin_filter: bool = False
    noop_suppress: bool = False
    hop_limit: int = 0          # 0 = off
    cap_per_product: int = 0    # 0 = off


@dataclass
class Agent:
    name: str
    reads: tuple
    writes: str
    produce: object             # function(product_dict, call_number) -> new value


@dataclass
class Result:
    calls: int = 0
    events: int = 0
    noop_skipped: int = 0
    echoes_ignored: int = 0
    hop_stops: int = 0
    cap_stops: int = 0
    max_hop: int = 0
    budget_hit: bool = False
    log: list = field(default_factory=list)


def run(products, edits, agents, guards, budget=500):
    """products: {id: {field: value}}; edits: [(product, field, value)] made by a human editor."""
    store = {pid: dict(fields) for pid, fields in products.items()}
    queue, res, next_id = deque(), Result(), [0]
    writes = {(a.name, pid): 0 for a in agents for pid in store}

    def publish(pid, fld, origin, causation, hop):
        next_id[0] += 1
        queue.append(Event(next_id[0], pid, fld, origin, causation, hop))
        res.events += 1
        res.max_hop = max(res.max_hop, hop)

    for pid, fld, value in edits:
        store[pid][fld] = value
        publish(pid, fld, 'editor', None, 0)
    processed = 0
    while queue:
        if processed >= budget:
            res.budget_hit = True
            break
        ev = queue.popleft()
        processed += 1
        for agent in agents:
            if guards.origin_filter and ev.origin == agent.name:
                res.echoes_ignored += 1
                continue
            if guards.hop_limit and ev.hop >= guards.hop_limit:
                res.hop_stops += 1
                continue
            if guards.cap_per_product and writes[(agent.name, ev.product)] >= guards.cap_per_product:
                res.cap_stops += 1
                continue
            res.calls += 1
            proposal = agent.produce(store[ev.product], res.calls)
            unchanged = canonical(proposal) == canonical(store[ev.product].get(agent.writes))
            if unchanged and guards.noop_suppress:
                res.noop_skipped += 1
                continue
            store[ev.product][agent.writes] = proposal
            writes[(agent.name, ev.product)] += 1
            publish(ev.product, agent.writes, agent.name, ev.id, ev.hop + 1)
            res.log.append((ev.id, agent.name, ev.product, agent.writes, ev.hop + 1))
    return store, res


# Scripted agents for the bookshop catalogue -------------------------------------------------------

def describe_stable(product, _call):
    """Deterministic: the description is a pure function of title and tags."""
    return 'A paperback edition of %s. Shelved under %s.' % (product['title'], ', '.join(product.get('tags', [])) or 'general')


def describe_drifting(product, call):
    """Imitates a model whose rewrite differs on every call, even with unchanged inputs."""
    return describe_stable(product, call) + ' (draft %d)' % call


def tag_from_description(product, _call):
    words = [w.strip('.,()').lower() for w in product.get('desc', '').split()]
    return sorted({w for w in words if w in {'paperback', 'fiction', 'classic', 'science'}} | {'catalogue'})


def tag_from_title(product, _call):
    """Breaks the data cycle: tags depend on the title only."""
    return sorted({'catalogue'} | ({'classic'} if 'Darkness' in product['title'] else set()))


DESCRIBE = Agent('describer', ('title', 'tags'), 'desc', describe_stable)
DESCRIBE_DRIFT = Agent('describer', ('title', 'tags'), 'desc', describe_drifting)
TAG = Agent('tagger', ('title', 'desc'), 'tags', tag_from_description)
TAG_TITLE = Agent('tagger', ('title',), 'tags', tag_from_title)

PRODUCTS = {'BK-4001': {'title': 'Kindred', 'tags': [], 'desc': ''},
            'BK-4002': {'title': 'The Left Hand of Darkness', 'tags': [], 'desc': ''}}
EDITS = [('BK-4001', 'title', 'Kindred (Anniversary Edition)'), ('BK-4002', 'title', 'The Left Hand of Darkness')]

SCENARIOS = {
    'drifting_agent_no_guards': ([DESCRIBE_DRIFT], Guards()),
    'drifting_agent_origin_filter': ([DESCRIBE_DRIFT], Guards(origin_filter=True)),
    'two_agents_origin_filter_only': ([DESCRIBE_DRIFT, TAG], Guards(origin_filter=True)),
    'two_stable_agents_noop_suppression': ([DESCRIBE, TAG], Guards(origin_filter=True, noop_suppress=True)),
    'two_agents_hop_limit_backstop': ([DESCRIBE_DRIFT, TAG], Guards(origin_filter=True, hop_limit=4)),
    'cycle_broken_in_the_data': ([DESCRIBE_DRIFT, TAG_TITLE], Guards(origin_filter=True, noop_suppress=True)),
}


def main():
    print('%-38s %6s %7s %6s %8s %8s %7s' % ('scenario', 'calls', 'events', 'hops', 'no-ops', 'hopstop', 'budget'))
    for name, (agents, guards) in SCENARIOS.items():
        _, r = run(PRODUCTS, EDITS, agents, guards)
        print('%-38s %6d %7d %6d %8d %8d %7s' % (name, r.calls, r.events, r.max_hop, r.noop_skipped, r.hop_stops, 'HIT' if r.budget_hit else 'ok'))


if __name__ == '__main__':
    main()
