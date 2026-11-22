# Author: Sandeep Belgavi. Token accounting across model retries, modelled on the behaviour that
# openai-agents-python 0.25.0 describes (PR 6046): usage the provider reports on failed or
# incomplete responses is counted, once per attempt. This is a standalone model, not the SDK, and
# makes no provider calls. Synthetic attempts for a help-desk agent at Belgavi's Book Store.
"""Run: python ledger.py"""
import json

ATTEMPTS = [  # what the provider returned on each physical attempt of one model call
    {'n': 1, 'status': 'incomplete', 'usage': {'input': 12, 'output': 16}},
    {'n': 2, 'status': 'connection_reset', 'usage': None},          # nothing reported
    {'n': 3, 'status': 'completed', 'usage': {'input': 12, 'output': 24}},
]


def total(u):
    return u['input'] + u['output']


def success_only(attempts):
    """Before: failed attempts add a request with zero tokens; only the success is counted."""
    ok = [a for a in attempts if a['status'] == 'completed']
    return {'requests': len(attempts), 'tokens': sum(total(a['usage']) for a in ok), 'unreported_attempts': 0}


def per_attempt(attempts):
    """After: every attempt with reported usage is counted exactly once, keyed by attempt number."""
    seen, tokens, unreported = {}, 0, 0
    for a in attempts:
        if a['usage'] is None:
            unreported += 1
            continue
        seen[a['n']] = a['usage']
    tokens = sum(total(u) for u in seen.values())
    return {'requests': len(attempts), 'tokens': tokens, 'unreported_attempts': unreported}


def double_counted(attempts):
    """A tempting bug: add usage when the error is raised and again when the retry loop finishes."""
    tokens = 0
    for a in attempts:
        if a['usage'] is not None:
            tokens += total(a['usage'])
            if a['status'] != 'completed':
                tokens += total(a['usage'])
    return {'requests': len(attempts), 'tokens': tokens}


def exhausted(attempts):
    """The loop gives up after two incomplete attempts: no response object, but usage was reported."""
    failed = [a for a in attempts if a['status'] != 'completed']
    return {'before': 0, 'after': sum(total(a['usage']) for a in failed if a['usage'])}


def budget_check(limit, ledger):
    return 'stop' if ledger['tokens'] >= limit else 'continue'


def run():
    before, after = success_only(ATTEMPTS), per_attempt(ATTEMPTS)
    give_up = [{'n': 1, 'status': 'incomplete', 'usage': {'input': 12, 'output': 16}},
               {'n': 2, 'status': 'incomplete', 'usage': {'input': 12, 'output': 18}}]
    return {'before': before, 'after': after, 'double_counted': double_counted(ATTEMPTS),
            'retries_exhausted': exhausted(give_up),
            'budget_60': {'before': budget_check(60, before), 'after': budget_check(60, after)}}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
