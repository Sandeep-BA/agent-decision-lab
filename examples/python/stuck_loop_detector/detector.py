"""Author: Sandeep Belgavi. Detecting stuck agent loops from tool-call fingerprints and a progress signal.

Companion to "Detecting Stuck Agent Loops" (aicassindra.com). Recorded synthetic runs are replayed through
the detector: an exact repeat, an A-B oscillation, a paraphrase loop, legitimate polling and a healthy run.
Arguments are normalised before hashing and volatile result fields are stripped. No model or tool is called.
"""
import hashlib
import json
from collections import deque

VOLATILE = {'request_id', 'fetched_at', 'latency_ms'}


def fp(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:16]


def strip_volatile(result):
    if isinstance(result, dict):
        return {k: strip_volatile(v) for k, v in result.items() if k not in VOLATILE}
    return result


class LoopDetector:
    def __init__(self, repeats=3, window=8, no_progress=8, polling=frozenset()):
        self.repeats, self.no_progress, self.polling = repeats, no_progress, polling
        self.recent = deque(maxlen=window)
        self.since_progress = 0

    def observe(self, tool, args, result, state):
        """Return a reason to stop, or None. state: the task fields that count as progress."""
        call, res, st = fp([tool, args]), fp([tool, strip_volatile(result)]), fp(state)
        progressed = not self.recent or st != self.recent[-1][2]
        self.since_progress = 0 if progressed else self.since_progress + 1
        self.recent.append((call, res, st, tool in self.polling))
        if tool in self.polling:
            return None
        same_call = sum(1 for c, r, s, poll in self.recent if c == call and r == res)
        same_result = sum(1 for c, r, s, poll in self.recent if r == res and not poll)
        if same_call >= self.repeats:
            return 'same call and result %d times' % same_call
        if not progressed and same_result >= self.repeats:
            return 'same result %d times without progress' % same_result
        if self.since_progress >= self.no_progress:
            return 'no progress for %d steps' % self.since_progress
        return None


def replay(steps, max_steps=30, **kw):
    """Replay recorded (tool, args, result, state) steps; return (steps taken, reason)."""
    det = LoopDetector(**kw)
    for i, (tool, args, result, state) in enumerate(steps, 1):
        reason = det.observe(tool, args, result, state)
        if reason:
            return i, reason
        if i >= max_steps:
            return i, 'step budget'
    return len(steps), 'finished'


def recorded_runs():
    st = {'case': 'CASE-6012', 'status': 'open'}
    runs = {}
    runs['exact'] = [('search_orders', {'q': 'CASE-6012'}, {'rows': [], 'request_id': i}, st) for i in range(40)]
    runs['oscillation'] = [(('get_return', {'case': 'CASE-6012'}, {'status': 'inspected'}, st) if i % 2 == 0
                            else ('get_refund', {'case': 'CASE-6012'}, {'refund': None}, st)) for i in range(40)]
    runs['paraphrase'] = [('search_kb', {'q': 'refund missing variant %d' % i}, {'hits': []}, st) for i in range(40)]
    poll = [('job_status', {'job': 'J-77'}, {'state': 'running', 'fetched_at': i}, st) for i in range(6)]
    poll.append(('job_status', {'job': 'J-77'}, {'state': 'done'}, dict(st, status='refund_issued')))
    poll.append(('send_reply', {'case': 'CASE-6012', 'template': 'refund_done'}, {'ok': True}, dict(st, status='replied')))
    runs['polling'] = poll
    healthy, state = [], dict(st)
    for i, tool in enumerate(['get_return', 'get_order', 'check_policy', 'issue_refund', 'send_reply']):
        if tool in ('issue_refund', 'send_reply'):
            state = dict(state, status=tool)
        healthy.append((tool, {'case': 'CASE-6012', 'step': i}, {'ok': i}, state))
    runs['healthy'] = healthy
    runs['reordered_args'] = [('search_orders', {'q': 'CASE-6012', 'limit': 5} if i % 2 else {'limit': 5, 'q': 'CASE-6012'},
                               {'rows': []}, st) for i in range(40)]
    return runs


def demo():
    out = []
    for name, steps in recorded_runs().items():
        out.append((name, replay(steps, polling=frozenset({'job_status'}))))
    out.append(('polling_not_exempt', replay(recorded_runs()['polling'])))
    out.append(('budget_only_exact', replay(recorded_runs()['exact'], repeats=99, no_progress=99)))
    return out


if __name__ == '__main__':
    for name, (steps, reason) in demo():
        print('%-20s %3d  %s' % (name, steps, reason))
