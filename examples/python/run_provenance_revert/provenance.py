"""Author: Sandeep Belgavi. Tag every agent write with its run and revert one bad run selectively.

SQLite (standard library). Each write goes through `write_field`, which updates the row and appends a
change-log entry (run, row, column, old value, new value) in the same transaction. `plan_revert` walks one
run's changes newest first: a field whose current value still equals what the run wrote is restored; a field
that someone changed later is a conflict and is left alone for a person, and by default
(row granularity) so is every other field of that row the run wrote. `apply_revert` writes its restores
through `write_field` too, under its own run id, so a revert is itself auditable and can be undone.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

SCHEMA = '''
CREATE TABLE cases (case_id TEXT PRIMARY KEY, status TEXT, credit REAL, note TEXT);
CREATE TABLE change_log (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL, actor TEXT NOT NULL, case_id TEXT NOT NULL, col TEXT NOT NULL,
  old_value, new_value, reverts_seq INTEGER);
CREATE INDEX change_log_run ON change_log(run_id);
'''
COLUMNS = {'status', 'credit', 'note'}


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(':memory:', isolation_level=None)
    db.executescript(SCHEMA)
    return db


def write_field(db, run_id: str, actor: str, case_id: str, col: str, value, reverts_seq=None):
    """One field update plus its provenance row, atomically."""
    assert col in COLUMNS
    db.execute('BEGIN IMMEDIATE')
    try:
        old = db.execute('SELECT %s FROM cases WHERE case_id = ?' % col, (case_id,)).fetchone()[0]
        db.execute('UPDATE cases SET %s = ? WHERE case_id = ?' % col, (value, case_id))
        db.execute('INSERT INTO change_log (run_id, actor, case_id, col, old_value, new_value, reverts_seq) VALUES (?,?,?,?,?,?,?)',
                   (run_id, actor, case_id, col, old, value, reverts_seq))
        db.execute('COMMIT')
    except Exception:
        db.execute('ROLLBACK')
        raise


@dataclass(frozen=True)
class Step:
    seq: int
    case_id: str
    col: str
    action: str     # 'restore', 'conflict' or 'already reverted'
    current: object
    restore_to: object


def plan_revert(db, run_id: str, granularity: str = 'row') -> list[Step]:
    """granularity='row': one conflicting field holds back every field of that row the run wrote."""
    done = {r[0] for r in db.execute('SELECT reverts_seq FROM change_log WHERE reverts_seq IS NOT NULL')}
    rows = db.execute('SELECT seq, case_id, col, old_value, new_value FROM change_log WHERE run_id = ? ORDER BY seq DESC',
                      (run_id,)).fetchall()
    plan, seen = [], set()
    for seq, case_id, col, old, new in rows:
        current = db.execute('SELECT %s FROM cases WHERE case_id = ?' % col, (case_id,)).fetchone()[0]
        if seq in done:
            plan.append(Step(seq, case_id, col, 'already reverted', current, old))
        elif (case_id, col) in seen:
            continue                      # an earlier write by the same run to the same field: the newest one decides
        elif current == new:
            # restore to the value before the run's FIRST write to this field
            first_old = db.execute('SELECT old_value FROM change_log WHERE run_id = ? AND case_id = ? AND col = ? ORDER BY seq LIMIT 1',
                                   (run_id, case_id, col)).fetchone()[0]
            plan.append(Step(seq, case_id, col, 'restore', current, first_old))
        else:
            plan.append(Step(seq, case_id, col, 'conflict', current, old))
        seen.add((case_id, col))
    if granularity == 'row':
        held = {s.case_id for s in plan if s.action == 'conflict'}
        plan = [Step(s.seq, s.case_id, s.col, 'conflict', s.current, s.restore_to) if s.case_id in held and s.action == 'restore' else s
                for s in plan]
    return plan


def apply_revert(db, run_id: str, operator: str, granularity: str = 'row') -> dict:
    counts = {'restore': 0, 'conflict': 0, 'already reverted': 0}
    for step in plan_revert(db, run_id, granularity):
        counts[step.action] += 1
        if step.action == 'restore':
            write_field(db, 'revert-' + run_id, operator, step.case_id, step.col, step.restore_to, reverts_seq=step.seq)
    return counts


def demo():
    db = connect()
    for cid in ('CASE-5201', 'CASE-5202', 'CASE-5203'):
        db.execute("INSERT INTO cases VALUES (?, 'open', 0, '')", (cid,))
    write_field(db, 'run-17', 'returns-agent', 'CASE-5201', 'status', 'approved')
    write_field(db, 'run-17', 'returns-agent', 'CASE-5201', 'credit', 25.0)
    write_field(db, 'run-17', 'returns-agent', 'CASE-5202', 'status', 'approved')
    write_field(db, 'run-17', 'returns-agent', 'CASE-5202', 'credit', 40.0)
    write_field(db, 'run-18', 'returns-agent', 'CASE-5203', 'status', 'approved')
    write_field(db, 'human', 'Geetha', 'CASE-5202', 'credit', 15.0)      # a later correction by a person
    return db


if __name__ == '__main__':
    db = demo()
    for s in plan_revert(db, 'run-17'):
        print('plan  %-10s %-7s %-10s current=%-9r restore_to=%r' % (s.case_id, s.col, s.action, s.current, s.restore_to))
    print('field-level would be', {(s.case_id, s.col): s.action for s in plan_revert(db, 'run-17', 'field')}[('CASE-5202', 'status')])
    print('apply', apply_revert(db, 'run-17', 'Jenya'))
    print('again', apply_revert(db, 'run-17', 'Jenya'))
    for row in db.execute('SELECT * FROM cases ORDER BY case_id'):
        print('row  ', row)
