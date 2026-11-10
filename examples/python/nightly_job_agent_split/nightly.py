"""A nightly reminder job where only the wording step is delegated to a drafter.

Author: Sandeep Belgavi. Selection, checkpointing, validation and the send ledger stay deterministic.
The drafter is any callable; tests use offline fakes, so no model is called.
"""
from dataclasses import dataclass, field
import datetime

TEMPLATE_VERSION = 'overdue-reminder-v1'
BANNED = ('refund', 'waive', 'free of charge', 'guarantee')


@dataclass
class State:
    checkpoint: str = ''                          # last order id fully handled in this run
    ledger: set = field(default_factory=set)      # idempotency keys already sent
    outbox: list = field(default_factory=list)    # (key, order_id, text)
    review: list = field(default_factory=list)    # (order_id, reason)
    retry: list = field(default_factory=list)     # (order_id, reason)


def select_due(orders, as_of):
    """Overdue, unreturned book loans, in a stable order. No model involvement."""
    due = [o for o in orders if not o['returned'] and datetime.date.fromisoformat(o['due']) < as_of]
    return sorted(due, key=lambda o: o['order_id'])


def key_for(run_date, order_id):
    return f'{run_date.isoformat()}:{order_id}:{TEMPLATE_VERSION}'


def check_draft(order, text):
    """Deterministic acceptance rule for a drafted message."""
    if not isinstance(text, str) or not text.strip():
        return 'empty draft'
    if len(text) > 600:
        return 'draft longer than 600 characters'
    if order['order_id'] not in text:
        return 'draft does not cite the order id'
    lowered = text.lower()
    for word in BANNED:
        if word in lowered:
            return f'draft makes a commitment the job may not make: {word!r}'
    return None


class Crash(Exception):
    """Raised by tests to stop a run between two durable steps."""


def run(orders, run_date, drafter, state, crash_after_send=None):
    """Process due orders after the checkpoint. Re-running the same run_date is safe."""
    for order in select_due(orders, run_date):
        oid = order['order_id']
        if state.checkpoint and oid <= state.checkpoint:
            continue
        key = key_for(run_date, oid)
        if key not in state.ledger:
            try:
                text = drafter(order)
            except Exception as exc:  # the drafter is untrusted and may fail
                state.retry.append((oid, type(exc).__name__))
                state.checkpoint = oid
                continue
            problem = check_draft(order, text)
            if problem:
                state.review.append((oid, problem))
                state.checkpoint = oid
                continue
            state.outbox.append((key, oid, text))
            state.ledger.add(key)
            if crash_after_send == oid:
                raise Crash(oid)       # the send is durable, the checkpoint is not yet
        state.checkpoint = oid
    return state


def fixture():
    return [
        {'order_id': 'ORD-201', 'reader': 'Geetha', 'title': 'Practical Rust', 'due': '2026-11-01', 'returned': False},
        {'order_id': 'ORD-202', 'reader': 'Jenya', 'title': 'Graph Theory', 'due': '2026-11-12', 'returned': False},
        {'order_id': 'ORD-203', 'reader': 'Tanishka', 'title': 'Poems', 'due': '2026-10-30', 'returned': True},
        {'order_id': 'ORD-204', 'reader': 'Dinky', 'title': 'Star Atlas', 'due': '2026-11-05', 'returned': False},
        {'order_id': 'ORD-205', 'reader': 'Hansini', 'title': 'Origami', 'due': '2026-11-08', 'returned': False},
    ]
