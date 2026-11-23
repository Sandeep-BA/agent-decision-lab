"""Who waits behind a slow sandbox start under each EnvironmentScope. Author: Sandeep Belgavi.

ADK Python 2.15.0 lets an environment declare `scope` (SHARED, USER or
SESSION). The environment and skill toolsets call `initialize` before every
tool call and hold a lock keyed by that scope: one key for SHARED, (app, user)
for USER and (app, user, session) for SESSION. A close waits for every
initialize call that has passed the close gate, whatever its key, and holds
new calls back until it has finished. The locks live in one process.

This is a discrete-time model of that behaviour, not ADK code. Time is in
tenths of a second. The environment keeps one sandbox per `resource` key; the
first initialize for a key is cold (creates the sandbox), later ones are warm.
Two calls that create the same sandbox at once are counted as duplicates:
that happens when the lock scope is narrower than the resource, or when calls
for one session reach two processes. Waiters are served first come, first
served; ADK polls its locks, so real ordering is not guaranteed. Standard
library only.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

COLD, WARM, CLOSE = 80, 1, 10       # tenths of a second


@dataclass(frozen=True)
class Call:
    id: str
    proc: str
    user: str
    session: str | None
    arrive: int


def key_for(scope: str, call: Call) -> tuple:
    if scope in ('USER', 'SESSION') and call.session is None:
        raise ValueError(f'{scope} scope needs a context that has a session ({call.id})')
    if scope == 'USER':
        return ('user', 'bookstore', call.user)
    if scope == 'SESSION':
        return ('session', 'bookstore', call.user, call.session)
    return ()                     # SHARED, or any unknown value


def resource_for(granularity: str, call: Call) -> tuple:
    return {'shared': (), 'user': (call.user,), 'session': (call.user, call.session)}[granularity]


def simulate(calls: list[Call], scope: str, resource: str = 'session', close_at: dict | None = None,
             limit: int = 2000) -> dict:
    close_at = dict(close_at or {})
    for c in calls:
        key_for(scope, c)                                  # fail before anything runs, as ADK does
    procs = sorted({c.proc for c in calls} | set(close_at))
    st = {p: {'created': set(), 'creating': {}, 'held': {}, 'queues': {}, 'gate': [], 'initializing': 0,
              'closing': False, 'close_start': None, 'close_end': None} for p in procs}
    rows = {c.id: {'id': c.id, 'proc': c.proc, 'user': c.user, 'session': c.session, 'arrive': c.arrive,
                   'start': None, 'end': None, 'cold': None} for c in calls}
    running = []                                           # (end, proc, call, lock key, resource key)
    duplicates = []
    by_tick = {}
    for c in calls:
        by_tick.setdefault(c.arrive, []).append(c)
    for t in range(limit + 1):
        for item in sorted([r for r in running if r[0] == t], key=lambda r: r[2].id):
            _, p, c, k, res = item
            running.remove(item)
            s = st[p]
            del s['held'][k]
            s['initializing'] -= 1
            if rows[c.id]['cold']:
                s['creating'][res] -= 1
                if not s['creating'][res]:
                    del s['creating'][res]
            s['created'].add(res)
            rows[c.id]['end'] = t
        for p in procs:
            s = st[p]
            if s['close_end'] == t:
                s['closing'], s['created'] = False, set()
            if p in close_at and close_at[p] == t:
                s['closing'] = True
            if s['closing'] and s['close_start'] is None and s['initializing'] == 0:
                s['close_start'], s['close_end'] = t, t + CLOSE
        for c in sorted(by_tick.get(t, []), key=lambda c: c.id):
            st[c.proc]['gate'].append(c)
        for p in procs:
            s = st[p]
            if not s['closing']:
                for c in s['gate']:
                    s['initializing'] += 1
                    s['queues'].setdefault(key_for(scope, c), []).append(c)
                s['gate'] = []
            for k in list(s['queues']):
                if k in s['held'] or not s['queues'][k]:
                    continue
                c = s['queues'][k].pop(0)
                res = resource_for(resource, c)
                cold = res not in s['created']
                if cold and res in s['creating']:
                    duplicates.append({'call': c.id, 'proc': p, 'resource': list(res), 'reason': 'same process, lock narrower than resource'})
                if cold:
                    s['creating'][res] = s['creating'].get(res, 0) + 1
                s['held'][k] = c.id
                rows[c.id].update(start=t, cold=cold)
                running.append((t + (COLD if cold else WARM), p, c, k, res))
        if t > max([c.arrive for c in calls] + list(close_at.values()) + [0]) and not running and \
                all(not s['gate'] and not any(s['queues'].values()) and (s['close_end'] is None or s['close_end'] <= t) for s in st.values()):
            break
    created = {}
    for r in rows.values():
        if r['cold']:
            c = next(x for x in calls if x.id == r['id'])
            created.setdefault(tuple(resource_for(resource, c)), []).append(r['proc'])
    cross = [{'resource': list(k), 'procs': v} for k, v in created.items() if len(set(v)) > 1]
    out = sorted(rows.values(), key=lambda r: (r['arrive'], r['id']))
    for r in out:
        r['wait'] = r['start'] - r['arrive']
    return {'scope': scope, 'resource': resource, 'calls': out,
            'max_wait': max(r['wait'] for r in out), 'total_wait': sum(r['wait'] for r in out),
            'duplicate_creations': duplicates, 'cross_process_creations': cross,
            'close': {p: [st[p]['close_start'], st[p]['close_end']] for p in close_at}}


CALLS = [Call('c1', 'A', 'jenya', 's1', 0), Call('c2', 'A', 'geetha', 's2', 5), Call('c3', 'A', 'jenya', 's1', 10),
         Call('c4', 'A', 'tanishka', 's3', 15), Call('c5', 'A', 'geetha', 's4', 20)]
LATE = Call('c6', 'A', 'jenya', 's1', 40)          # arrives while the close waits
TWO_PROCS = [Call('c1', 'A', 'jenya', 's1', 0), Call('c2', 'B', 'jenya', 's1', 3)]


def run() -> dict:
    return {
        'shared': simulate(CALLS, 'SHARED'),
        'user': simulate(CALLS, 'USER'),
        'session': simulate(CALLS, 'SESSION'),
        'session_scope_user_resource': simulate(CALLS, 'SESSION', resource='user'),
        'session_with_close_at_3s': simulate(CALLS + [LATE], 'SESSION', close_at={'A': 30}),
        'two_processes': simulate(TWO_PROCS, 'SESSION'),
    }


def summary(r: dict) -> str:
    waits = ' '.join(f"{c['id']}={c['wait'] / 10:.1f}" for c in r['calls'])
    return (f"{r['scope']:<8} resource={r['resource']:<8} waits(s): {waits}  max={r['max_wait'] / 10:.1f}s "
            f"dups={len(r['duplicate_creations'])} cross={len(r['cross_process_creations'])} close={r['close']}")


if __name__ == '__main__':
    for name, r in run().items():
        print(f'{name:<28}', summary(r))
    print(json.dumps(run()['session_with_close_at_3s']['calls']))
