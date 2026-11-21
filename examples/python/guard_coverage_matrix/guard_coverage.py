"""Exhaustive guard coverage for one workflow state. Author: Sandeep Belgavi.

A refund request at the fictional Belgavi's Book Store waits in the `review`
state. Three boolean facts decide where it goes next. With three facts there
are only eight input combinations, so every guard can be checked against every
combination before the workflow is allowed to run.

Strict routing refuses a state machine with any gap (no guard matches) or any
overlap (two or more guards match). Priority routing picks the first matching
transition in document order, the way SCXML selects among enabled transitions
in one state, and reports which combinations it resolved silently.
"""
from itertools import product

FACTS = ('verified', 'over_limit', 'confident')


def t(name, target, guard, text):
    return {'name': name, 'target': target, 'guard': guard, 'text': text}


FIXTURES = {
    'complete': [
        t('T1', 'auto_refund', lambda f: f['verified'] and not f['over_limit'] and f['confident'],
          'verified and not over_limit and confident'),
        t('T2', 'human_review', lambda f: f['verified'] and (f['over_limit'] or not f['confident']),
          'verified and (over_limit or not confident)'),
        t('T3', 'verify_identity', lambda f: not f['verified'], 'not verified'),
    ],
    # T2 forgot the "not confident" half: one combination has no route.
    'gap': [
        t('T1', 'auto_refund', lambda f: f['verified'] and not f['over_limit'] and f['confident'],
          'verified and not over_limit and confident'),
        t('T2', 'human_review', lambda f: f['verified'] and f['over_limit'], 'verified and over_limit'),
        t('T3', 'verify_identity', lambda f: not f['verified'], 'not verified'),
    ],
    # T1 dropped "verified": an unverified, small, confident request matches T1 and T3.
    'overlap': [
        t('T1', 'auto_refund', lambda f: not f['over_limit'] and f['confident'], 'not over_limit and confident'),
        t('T2', 'human_review', lambda f: f['verified'] and (f['over_limit'] or not f['confident']),
          'verified and (over_limit or not confident)'),
        t('T3', 'verify_identity', lambda f: not f['verified'], 'not verified'),
    ],
}

FALLBACK = t('T9', 'escalate_to_person', lambda f: True, 'fallback when nothing else matches')


def combinations():
    for values in product((False, True), repeat=len(FACTS)):
        yield dict(zip(FACTS, values))


def label(facts):
    return ', '.join(f'{k}={"T" if v else "F"}' for k, v in facts.items())


def analyse(transitions, order='document', fallback=False):
    """Return one row per combination plus totals. Pure function; no I/O."""
    ordered = list(transitions) if order == 'document' else list(reversed(transitions))
    rows = []
    chosen_counts = {x['name']: 0 for x in ordered}
    for facts in combinations():
        matches = [x['name'] for x in ordered if x['guard'](facts)]
        if len(matches) == 1:
            kind = 'ok'
        elif not matches:
            kind = 'gap'
        else:
            kind = 'overlap'
        priority_pick = matches[0] if matches else (FALLBACK['name'] if fallback else None)
        if priority_pick in chosen_counts:
            chosen_counts[priority_pick] += 1
        rows.append({'facts': label(facts), 'matches': matches, 'kind': kind, 'priority_pick': priority_pick})
    gaps = [r for r in rows if r['kind'] == 'gap']
    overlaps = [r for r in rows if r['kind'] == 'overlap']
    return {
        'rows': rows,
        'gaps': len(gaps),
        'overlaps': len(overlaps),
        'strict_accepts': not overlaps and (not gaps or fallback),
        'unrouted_in_priority': 0 if fallback else len(gaps),
        'silently_resolved': len(overlaps),
        'never_chosen': sorted(k for k, v in chosen_counts.items() if v == 0),
    }


def route(transitions, facts, mode='strict', order='document', fallback=False):
    """Route one request. Strict mode refuses a machine that failed analysis."""
    report = analyse(transitions, order, fallback)
    if mode == 'strict' and not report['strict_accepts']:
        raise ValueError(f"refused: {report['gaps']} gap(s), {report['overlaps']} overlap(s)")
    ordered = list(transitions) if order == 'document' else list(reversed(transitions))
    for x in ordered:
        if x['guard'](facts):
            return x['target']
    if fallback:
        return FALLBACK['target']
    raise LookupError('no transition matches ' + label(facts))


def main():
    for name, transitions in FIXTURES.items():
        r = analyse(transitions)
        print(f"{name}: gaps={r['gaps']} overlaps={r['overlaps']} strict_accepts={r['strict_accepts']}")
        for row in r['rows']:
            if row['kind'] != 'ok':
                print(f"  {row['kind']:7} {row['facts']} matches={row['matches']} priority_pick={row['priority_pick']}")
    risky = {'verified': False, 'over_limit': False, 'confident': True}
    print('overlap fixture, priority routing, unverified small confident request ->',
          route(FIXTURES['overlap'], risky, mode='priority'))
    try:
        route(FIXTURES['overlap'], risky, mode='strict')
    except ValueError as e:
        print('overlap fixture, strict routing ->', e)
    print('gap fixture with fallback, strict accepts =', analyse(FIXTURES['gap'], fallback=True)['strict_accepts'])


if __name__ == '__main__':
    main()
