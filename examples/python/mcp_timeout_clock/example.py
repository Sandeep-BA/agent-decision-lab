"""Model of an MCP client request clock: idle timeout, reset on progress and a maximum total.
Author: Sandeep Belgavi.

Two ceiling modes are modelled:
  sdk    - the ceiling is checked only when a progress notification arrives, as in the TypeScript SDK's
           Protocol._resetTimeout (main branch, read 2026-11-27). A request whose progress stops can then
           wait one more idle timeout past the ceiling, and that path rejects without sending
           notifications/cancelled.
  timer  - the ceiling is its own timer (for example an AbortSignal.timeout passed as the request signal),
           so it fires at the ceiling and the client sends a cancellation.
Times are milliseconds after the request is sent. Synthetic scenarios; no MCP server is contacted.
"""
import json, sys

SCENARIOS = {
    'steady-progress': {'timeout': 60000, 'reset': True, 'max_total': 300000, 'mode': 'sdk',
                        'progress': [20000, 40000, 60000, 80000, 100000], 'response': 110000},
    'no-reset-long-job': {'timeout': 60000, 'reset': False, 'max_total': 0, 'mode': 'sdk',
                          'progress': [20000, 40000, 60000], 'response': 90000},
    'chatty-forever': {'timeout': 60000, 'reset': True, 'max_total': 300000, 'mode': 'sdk',
                       'progress': list(range(25000, 600001, 25000)), 'response': None},
    'chatty-forever-timer': {'timeout': 60000, 'reset': True, 'max_total': 300000, 'mode': 'timer',
                             'progress': list(range(25000, 600001, 25000)), 'response': None},
    'stalls-before-ceiling': {'timeout': 60000, 'reset': True, 'max_total': 300000, 'mode': 'sdk',
                              'progress': [50000, 100000, 150000, 200000, 250000, 290000], 'response': None},
    'stalls-before-ceiling-timer': {'timeout': 60000, 'reset': True, 'max_total': 300000, 'mode': 'timer',
                                    'progress': [50000, 100000, 150000, 200000, 250000, 290000], 'response': None},
}


def simulate(timeout, reset, max_total, mode, progress, response):
    """Return the outcome, when the client stopped waiting, whether it sent a cancellation, and a trace."""
    if timeout <= 0:
        raise ValueError('timeout must be positive')
    if mode not in ('sdk', 'timer'):
        raise ValueError('mode must be sdk or timer')
    trace = [f'0 ms: request sent; idle deadline {timeout} ms' + (f'; ceiling {max_total} ms ({mode})' if max_total else '')]
    deadline, resets = timeout, 0
    events = sorted([(p, 'progress') for p in progress if p >= 0] + ([(response, 'response')] if response is not None else []))
    hard = max_total if (max_total and mode == 'timer') else None
    for at, kind in events:
        fire = min(deadline, hard) if hard is not None else deadline
        if at >= fire:
            break
        if kind == 'response':
            trace.append(f'{at} ms: result received before the deadline')
            return finish('result', at, False, resets, trace, response, at)
        if not reset:
            trace.append(f'{at} ms: progress received; clock not reset (deadline stays {deadline} ms)')
            continue
        if max_total and mode == 'sdk' and at >= max_total:
            trace.append(f'{at} ms: progress received after the {max_total} ms ceiling; request rejected, no notifications/cancelled sent')
            return finish('max-total-exceeded', at, False, resets, trace, response, at)
        deadline, resets = at + timeout, resets + 1
        trace.append(f'{at} ms: progress received; idle deadline moved to {deadline} ms')
    fire = min(deadline, hard) if hard is not None else deadline
    if hard is not None and fire == hard and hard <= deadline:
        trace.append(f'{hard} ms: ceiling timer fired; notifications/cancelled sent')
        return finish('ceiling-cancelled', hard, True, resets, trace, response, hard)
    trace.append(f'{deadline} ms: idle timeout fired; notifications/cancelled sent')
    return finish('idle-timeout', deadline, True, resets, trace, response, deadline)


def finish(outcome, ended, cancel_sent, resets, trace, response, at):
    if response is not None and response > at and outcome != 'result':
        trace.append(f'{response} ms: late result arrives and is ignored; check whether the work already took effect')
    return {'outcome': outcome, 'stopped_waiting_ms': ended, 'cancellation_sent': cancel_sent,
            'progress_resets': resets, 'late_result_ignored': bool(response is not None and response > at and outcome != 'result'),
            'trace': trace}


def worst_case_wait(timeout, max_total, mode):
    """Upper bound on how long a request can keep the caller waiting while progress keeps arriving and then stops."""
    if not max_total:
        return None
    return max_total if mode == 'timer' else max_total + timeout


def main():
    out = {name: simulate(**s) for name, s in SCENARIOS.items()}
    out['worst_case_wait_ms'] = {'sdk': worst_case_wait(60000, 300000, 'sdk'), 'timer': worst_case_wait(60000, 300000, 'timer')}
    json.dump(out, sys.stdout, indent=2); print()
    return out


if __name__ == '__main__':
    main()
