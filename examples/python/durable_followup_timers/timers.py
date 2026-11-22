# Author: Sandeep Belgavi. Durable follow-up timers for help-desk cases at the fictional
# Belgavi's Book Store. Synthetic data, standard library only (sqlite3), no model calls.
"""Compare an in-memory sleep with a durable timer table.

The agent asks the customer a question and must follow up if no reply arrives.
Run: python timers.py
"""
import datetime as dt
import json
import sqlite3

UTC = dt.timezone.utc
SCHEMA = """
CREATE TABLE timers (
  case_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  due_at TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('pending','claimed','fired','cancelled')),
  claimed_by TEXT,
  PRIMARY KEY (case_id, kind)
);
CREATE TABLE outbox (case_id TEXT NOT NULL, message TEXT NOT NULL, timer_kind TEXT NOT NULL,
  UNIQUE (case_id, timer_kind));
"""


def due_time(asked_at: dt.datetime, wait_days: int = 2) -> dt.datetime:
    """Deterministic rule: wait_days later at 09:00 UTC, moved off Saturday/Sunday."""
    d = (asked_at + dt.timedelta(days=wait_days)).date()
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    return dt.datetime(d.year, d.month, d.day, 9, 0, tzinfo=UTC)


def connect():
    db = sqlite3.connect(':memory:', isolation_level=None)
    db.executescript(SCHEMA)
    return db


def schedule(db, case_id, asked_at):
    due = due_time(asked_at)
    # Re-asking replaces the pending timer instead of adding a second one.
    db.execute("INSERT INTO timers VALUES (?, 'followup', ?, 'pending', NULL) "
               "ON CONFLICT(case_id, kind) DO UPDATE SET due_at=excluded.due_at, state='pending', claimed_by=NULL",
               (case_id, due.isoformat()))
    return due


def customer_replied(db, case_id):
    """Cancel only if the timer has not been claimed; returns True when the reply won."""
    cur = db.execute("UPDATE timers SET state='cancelled' WHERE case_id=? AND kind='followup' AND state='pending'", (case_id,))
    return cur.rowcount == 1


def claim_due(db, worker, now):
    """Compare-and-set claim: each due timer is claimed by exactly one worker."""
    rows = db.execute("SELECT case_id FROM timers WHERE state='pending' AND due_at <= ? ORDER BY due_at, case_id",
                      (now.isoformat(),)).fetchall()
    won = []
    for (case_id,) in rows:
        cur = db.execute("UPDATE timers SET state='claimed', claimed_by=? WHERE case_id=? AND kind='followup' AND state='pending'",
                         (worker, case_id))
        if cur.rowcount == 1:
            won.append(case_id)
    return won


def fire(db, case_id):
    """Write the follow-up and mark the timer fired in one transaction."""
    db.execute('BEGIN')
    db.execute("INSERT OR IGNORE INTO outbox VALUES (?, ?, 'followup')",
               (case_id, f'Following up on {case_id}: do you still need help with your order?'))
    db.execute("UPDATE timers SET state='fired' WHERE case_id=? AND kind='followup' AND state='claimed'", (case_id,))
    db.execute('COMMIT')


def sleep_in_loop(cases, restart_after_hours):
    """In-memory model: a wait lives in the process, so a restart forgets it."""
    sent = []
    for case_id, asked_at in cases:
        due = due_time(asked_at)
        if (due - asked_at) <= dt.timedelta(hours=restart_after_hours):
            sent.append(case_id)
    return sent


def run():
    asked = dt.datetime(2026, 11, 20, 15, 30, tzinfo=UTC)  # a Friday
    cases = [('CASE-4101', asked), ('CASE-4102', asked + dt.timedelta(hours=1)), ('CASE-4103', asked + dt.timedelta(hours=2))]
    out = {'due': {c: due_time(a).isoformat() for c, a in cases}}
    # A deploy restarts the process 20 hours after the questions were asked.
    out['sleep_in_loop_sent'] = sleep_in_loop(cases, restart_after_hours=20)

    db = connect()
    for c, a in cases:
        schedule(db, c, a)
    # Jenya replies on CASE-4102 before the timer is due.
    out['reply_cancelled_4102'] = customer_replied(db, 'CASE-4102')
    now = dt.datetime(2026, 11, 23, 9, 0, 5, tzinfo=UTC)
    first, second = claim_due(db, 'worker-a', now), claim_due(db, 'worker-b', now)
    out['claims'] = {'worker-a': first, 'worker-b': second}
    # Geetha replies on CASE-4103 after worker-a claimed it: the reply loses the race.
    out['late_reply_cancelled_4103'] = customer_replied(db, 'CASE-4103')
    for c in first:
        fire(db, c)
    fire(db, 'CASE-4101')  # a retried fire after a crash must not send twice
    out['outbox'] = [r[0] for r in db.execute('SELECT case_id FROM outbox ORDER BY case_id')]
    out['states'] = dict(db.execute('SELECT case_id, state FROM timers ORDER BY case_id').fetchall())
    return out


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
