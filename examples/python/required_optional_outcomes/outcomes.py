"""Required versus optional work in one agent workflow step. Author: Sandeep Belgavi.

A refund case, CASE-6101, at the fictional Belgavi's Book Store runs four
pieces of work. Two are required (look up the order, compute the refund) and
two are optional agent checks (a tone review of the reply, a reading
suggestion). The workflow outcome must come from the required work; optional
work can only add warnings.

`naive_taskgroup` puts all four in one asyncio.TaskGroup: when an optional
check raises, the group cancels the required work too. `separated` gives each
optional task its own error and deadline handling and derives the outcome
with `derive_outcome`, a pure function that also refuses unapproved skips.
"""
import asyncio

REQUIRED = ('order_lookup', 'refund_amount')
OPTIONAL = ('tone_review', 'reading_suggestion')
DURATIONS = {'order_lookup': 0.08, 'refund_amount': 0.12, 'tone_review': 0.02, 'reading_suggestion': 0.10}


async def work(name, fail=(), slow=()):
    await asyncio.sleep(DURATIONS[name] * (10 if name in slow else 1))
    if name in fail:
        raise RuntimeError(name + ' failed')
    return name + ' ok'


def derive_outcome(states, skips=None):
    """states: name -> ok | failed | cancelled | timed_out | pending | skipped.
    skips: name -> approval reference for an intentionally skipped task."""
    skips = skips or {}
    unknown = set(states) - set(REQUIRED) - set(OPTIONAL)
    if unknown:
        raise ValueError('unknown task ' + ', '.join(sorted(unknown)))
    missing = [n for n in REQUIRED + OPTIONAL if n not in states]
    if missing:
        raise ValueError('no state recorded for ' + ', '.join(missing))
    warnings, problems = [], []
    for name in REQUIRED:
        s = states[name]
        if s == 'skipped' and name in skips:
            warnings.append(f'{name} skipped with approval {skips[name]}')
        elif s == 'pending':
            return {'outcome': 'running', 'warnings': warnings, 'problems': [name + ' still pending']}
        elif s != 'ok':
            problems.append(f'{name} {s}' + (' without approval' if s == 'skipped' else ''))
    for name in OPTIONAL:
        s = states[name]
        if s == 'pending':
            problems.append(name + ' still pending at the decision point')
        elif s == 'skipped' and name not in skips:
            problems.append(name + ' skipped without a recorded reason')
        elif s != 'ok':
            warnings.append(f'{name} {s}')
    if problems:
        return {'outcome': 'failed', 'warnings': warnings, 'problems': problems}
    return {'outcome': 'succeeded_with_warnings' if warnings else 'succeeded', 'warnings': warnings, 'problems': []}


async def naive_taskgroup(fail=(), slow=()):
    tasks = {}
    try:
        async with asyncio.TaskGroup() as tg:
            for name in REQUIRED + OPTIONAL:
                tasks[name] = tg.create_task(work(name, fail, slow))
    except* RuntimeError:
        pass
    states = {}
    for name, task in tasks.items():
        if task.cancelled():
            states[name] = 'cancelled'
        elif task.exception() is not None:
            states[name] = 'failed'
        else:
            states[name] = 'ok'
    return states


async def separated(fail=(), slow=(), optional_deadline=0.3):
    async def optional(name):
        try:
            await asyncio.wait_for(work(name, fail, slow), optional_deadline)
            return 'ok'
        except TimeoutError:
            return 'timed_out'
        except RuntimeError:
            return 'failed'

    async with asyncio.TaskGroup() as tg:
        required = {n: tg.create_task(work(n, fail, slow)) for n in REQUIRED if n not in fail}
        extra = {n: tg.create_task(optional(n)) for n in OPTIONAL}
    states = {n: 'ok' for n in required}
    states.update({n: 'failed' for n in REQUIRED if n in fail})
    states.update({n: t.result() for n, t in extra.items()})
    return states


def main():
    naive = asyncio.run(naive_taskgroup(fail={'tone_review'}))
    print('naive TaskGroup, tone_review fails:', naive, '->', derive_outcome(naive)['outcome'])
    sep = asyncio.run(separated(fail={'tone_review'}))
    print('separated, tone_review fails:', sep, '->', derive_outcome(sep))
    slow = asyncio.run(separated(slow={'reading_suggestion'}))
    print('separated, reading_suggestion slow:', slow, '->', derive_outcome(slow)['outcome'])
    print('skip without reason:', derive_outcome({**sep, 'tone_review': 'skipped'})['outcome'])
    print('skip with approval:', derive_outcome({**sep, 'tone_review': 'skipped'}, {'tone_review': 'APPROVAL-17'})['outcome'])


if __name__ == '__main__':
    main()
