"""Orchestrator-owned fan-in for parallel agent subtasks. Author: Sandeep Belgavi.

Three reviewer subtasks check whether a refund on a help-desk case at the
fictional Belgavi's Book Store is within policy, and a fourth fails. The
orchestrator, not a model, decides when the join completes:

- all: wait for every subtask (or the deadline);
- quorum: stop when k results agree on the same verdict;
- first_valid: stop at the first well-formed result.

Results that finish after the decision are recorded as late and never change
it; subtasks still running are listed for cancellation. The decision record
names exactly which results it used. Time is simulated (seconds after
dispatch), so every outcome is deterministic. Standard library only.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import json


@dataclass(frozen=True)
class Subtask:
    id: str
    finishes_at: float          # simulated seconds after dispatch
    verdict: str | None         # 'approve' / 'reject'; None means the subtask failed
    error: str = ''


SUBTASKS = [
    Subtask('policy-reader', 0.8, 'approve'),
    Subtask('order-history', 2.5, 'approve'),
    Subtask('fraud-signals', 9.0, 'reject'),
    Subtask('payment-check', 1.2, None, 'timeout calling payment service'),
]


def join(subtasks: list[Subtask], policy: str, deadline: float, k: int = 2, required: tuple = ()) -> dict:
    if policy not in ('all', 'quorum', 'first_valid'):
        raise ValueError('policy must be all, quorum or first_valid')
    if deadline <= 0 or k < 1:
        raise ValueError('deadline must be positive and k at least 1')
    events = sorted(subtasks, key=lambda s: (s.finishes_at, s.id))
    pending_required = set(required)
    used, failed, trace = [], [], []
    decided_at, verdict, reason = None, None, None
    for s in events:
        if s.finishes_at > deadline:
            break
        if s.verdict is None:
            failed.append(s.id)
            trace.append(f't={s.finishes_at:.1f}s {s.id} failed: {s.error}')
        else:
            used.append(s)
            trace.append(f't={s.finishes_at:.1f}s {s.id} -> {s.verdict}')
        pending_required.discard(s.id)
        if s.id in required and s.verdict == 'reject':
            used = [s]
            decided_at, verdict, reason = s.finishes_at, 'reject', f'required check {s.id} rejected'
            break
        if pending_required:
            continue
        if policy == 'first_valid' and used:
            decided_at, verdict, reason = s.finishes_at, used[0].verdict, 'first well-formed result'
            break
        if policy == 'quorum':
            for v in ('approve', 'reject'):
                agreeing = [u for u in used if u.verdict == v]
                if len(agreeing) >= k:
                    used = agreeing
                    decided_at, verdict, reason = s.finishes_at, v, f'{k} results agree'
                    break
            if verdict:
                break
    if policy == 'all' and verdict is None:
        finished = [s for s in events if s.finishes_at <= deadline]
        if len(finished) == len(events):
            verdicts = {u.verdict for u in used}
            decided_at = max(s.finishes_at for s in events)
            if failed:
                verdict, reason = 'escalate', 'a subtask failed, so "all" cannot be satisfied'
            elif len(verdicts) == 1:
                verdict, reason = verdicts.pop(), 'all results agree'
            else:
                verdict, reason = 'escalate', 'results disagree'
    if verdict is None:
        decided_at, verdict, reason = deadline, 'escalate', f'deadline {deadline:.1f}s reached without satisfying {policy}'
        trace.append(f't={deadline:.1f}s deadline')
    late = [s.id for s in events if s.finishes_at > decided_at]
    trace.append(f'decision at t={decided_at:.1f}s: {verdict} ({reason}); cancel {late or "nothing"}')
    return {'policy': policy, 'k': k if policy == 'quorum' else None, 'deadline': deadline,
            'decided_at': decided_at, 'verdict': verdict, 'reason': reason,
            'used': [u.id for u in used], 'failed': failed, 'cancel_or_ignore_late': late, 'trace': trace}


def run() -> list[dict]:
    return [join(SUBTASKS, 'all', 12.0), join(SUBTASKS, 'all', 5.0), join(SUBTASKS, 'quorum', 5.0, 2),
            join(SUBTASKS, 'quorum', 5.0, 3), join(SUBTASKS, 'first_valid', 5.0)]


if __name__ == '__main__':
    for r in run():
        print(json.dumps({k: v for k, v in r.items() if k != 'trace'}))
        for line in r['trace']:
            print('   ', line)
