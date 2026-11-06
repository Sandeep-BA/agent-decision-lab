"""Classify flaky agent evaluation cases from replayed and live runs, with planted harness faults.

Author: Sandeep Belgavi. Companion to "Flaky Agent Evaluation Cases: Harness Bugs Versus Model Variance"
(aicassindra.com). Standard library only. The "model" is a recorded response or a seeded sampler; nothing is
called over the network.
"""
import datetime as dt
import math
import random
from collections import Counter

FIXTURE_ORDER_DATE = dt.date(2026, 10, 1)
RETURN_DAYS = 30


def return_window_open(order_date, today):
    return (today - order_date).days <= RETURN_DAYS


def case_6001(clock):
    """CASE-6001: can Dinky return a cookbook bought on 1 October? Expected answer written on 10 October: yes."""
    return return_window_open(FIXTURE_ORDER_DATE, clock())


def recommend(titles):
    """A tool that builds its answer from a set; order differs between processes with hash randomisation."""
    return list(set(titles))


class SharedSandbox:
    def __init__(self):
        self.orders = {'BK-401': 'placed'}


def case_cancel_status(sandbox, parallel_neighbour_runs):
    if parallel_neighbour_runs:
        sandbox.orders['BK-401'] = 'cancelled'      # another case in the same sandbox cancels the order
    return sandbox.orders['BK-401'] == 'placed'


def classify(runs):
    """runs: dicts with mode ('replay' or 'live'), parallel (bool), passed (bool), error (str or None)."""
    def varies(rs):
        return len({r['passed'] for r in rs}) > 1
    replay = [r for r in runs if r['mode'] == 'replay']
    live = [r for r in runs if r['mode'] == 'live']
    if any(r['error'] for r in runs):
        kinds = Counter(r['error'] for r in runs if r['error'])
        return 'infrastructure: ' + kinds.most_common(1)[0][0]
    if varies(replay):
        serial = [r for r in replay if not r['parallel']]
        return 'shared state' if serial and not varies(serial) else 'harness'
    if varies(live):
        return 'model variance'
    return 'stable'


def runs_needed(failure_rate, confidence=0.95):
    """Clean runs needed to see at least one failure with the given confidence."""
    return math.ceil(math.log(1 - confidence) / math.log(1 - failure_rate))


def pass_hat_k(successes, trials, k):
    """Unbiased estimate of pass^k (all k of k trials succeed) from n trials with c successes."""
    if k > trials:
        raise ValueError('k cannot exceed the number of trials')
    return math.comb(successes, k) / math.comb(trials, k)


def simulate_live(p_success, n, seed):
    rng = random.Random(seed)
    return [{'mode': 'live', 'parallel': False, 'passed': rng.random() < p_success, 'error': None} for _ in range(n)]


if __name__ == '__main__':
    import json
    real_clock = lambda: dt.date(2026, 11, 6)
    frozen = lambda: FIXTURE_ORDER_DATE + dt.timedelta(days=10)
    print(json.dumps({'case_6001_real_clock': case_6001(real_clock), 'case_6001_frozen_clock': case_6001(frozen)}))
    shared = [{'mode': 'replay', 'parallel': i % 2 == 0, 'passed': i % 2 == 1, 'error': None} for i in range(6)]
    print(json.dumps({'shared_state_case': classify(shared),
                      'live_case': classify([{'mode': 'replay', 'parallel': False, 'passed': True, 'error': None}] * 3 + simulate_live(0.8, 20, 7)),
                      'runs_needed_5pct': runs_needed(0.05), 'runs_needed_20pct': runs_needed(0.20),
                      'pass_hat_4_of_16_with_12': round(pass_hat_k(12, 16, 4), 3)}))
