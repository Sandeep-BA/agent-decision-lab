# Author: Sandeep Belgavi. Join agent decision records to later case outcomes for the fictional
# Belgavi's Book Store help desk. Synthetic cases from a seeded generator; no model calls.
"""Naive before/after comparison versus a randomized holdout and a closed attribution window.

Run: python join.py
"""
import json
import random

WINDOW_DAYS = 7
# Synthetic ground truth used only to generate data: probability that a case is reopened.
REOPEN = {('easy', 'person'): 0.08, ('easy', 'agent'): 0.10, ('hard', 'person'): 0.30}


def generate(n=1000, seed=20261122, holdout=0.2):
    rng = random.Random(seed)
    decisions, outcomes = [], []
    for i in range(n):
        case_id = f'CASE-{5000 + i}'
        difficulty = 'easy' if rng.random() < 0.6 else 'hard'
        eligible = difficulty == 'easy'  # the agent is only offered easy cases
        arm = 'person'
        if eligible:
            arm = 'person' if rng.random() < holdout else 'agent'
        day = rng.randrange(0, 21)
        decisions.append({'case_id': case_id, 'decision_id': f'D-{i}', 'policy': 'refund-assist-v3',
                          'eligible': eligible, 'arm': arm, 'decided_day': day})
        if rng.random() < REOPEN[(difficulty, arm)]:
            outcomes.append({'case_id': case_id, 'reopened_day': day + rng.randrange(1, 11)})
    return decisions, outcomes


def join(decisions, outcomes, as_of_day, window=WINDOW_DAYS):
    """Attribute a reopen to a decision only inside [decided, decided + window], and only
    once the window has closed by as_of_day. Open windows are reported, not counted."""
    reopened = {}
    for o in outcomes:
        reopened.setdefault(o['case_id'], []).append(o['reopened_day'])
    rows = []
    for d in decisions:
        closes = d['decided_day'] + window
        hit = any(d['decided_day'] < day <= closes and day <= as_of_day for day in reopened.get(d['case_id'], []))
        rows.append({**d, 'window_closed': closes <= as_of_day, 'reopened': hit})
    return rows


def rate(rows):
    return (sum(r['reopened'] for r in rows), len(rows))


def summarize(rows, closed_only=True):
    use = [r for r in rows if r['window_closed']] if closed_only else rows
    agent = [r for r in use if r['arm'] == 'agent']
    person_all = [r for r in use if r['arm'] == 'person']
    holdout = [r for r in use if r['arm'] == 'person' and r['eligible']]
    return {'cases': len(use), 'open_windows_excluded': len(rows) - len(use),
            'agent': rate(agent), 'all_person_cases': rate(person_all), 'eligible_holdout': rate(holdout)}


def pct(pair):
    k, n = pair
    return round(100 * k / n, 1) if n else None


def diff_interval(a, b, z=1.96):
    """Difference of two proportions (a - b) in points with a normal-approximation 95% interval."""
    (ka, na), (kb, nb) = a, b
    pa, pb = ka / na, kb / nb
    se = (pa * (1 - pa) / na + pb * (1 - pb) / nb) ** 0.5
    d = pa - pb
    return [round(100 * x, 1) for x in (d, d - z * se, d + z * se)]


def run():
    decisions, outcomes = generate()
    final = summarize(join(decisions, outcomes, as_of_day=40))
    early = summarize(join(decisions, outcomes, as_of_day=24), closed_only=False)
    return {
        'final': final,
        'final_pct': {k: pct(final[k]) for k in ('agent', 'all_person_cases', 'eligible_holdout')},
        'naive_diff': diff_interval(final['agent'], final['all_person_cases']),
        'holdout_diff': diff_interval(final['agent'], final['eligible_holdout']),
        'early_unclosed': early,
        'early_unclosed_pct': {k: pct(early[k]) for k in ('agent', 'all_person_cases', 'eligible_holdout')},
    }


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
