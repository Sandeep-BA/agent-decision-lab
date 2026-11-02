# Run provenance and selective revert

**Author: Sandeep Belgavi**

A runnable companion to *Tagging Agent Writes With Run Provenance* (aicassindra.com, System Design). A returns
agent at Belgavi's Book Store updates help-desk cases. Every write goes through `write_field`, which updates the
row and appends a change-log entry (run id, actor, case, column, old value, new value) in the same SQLite
transaction. `plan_revert(run_id)` walks one run's changes newest first. A field whose current value still
equals what the run wrote is restored to its value before the run's first write. A field that someone changed
later is a conflict, and by default (row granularity) every other field the run wrote on that row is held back
too, so a case is never left half reverted. `apply_revert` writes restores through `write_field` under the run
id `revert-<run>`, so a revert is auditable and can itself be reverted.

**No model is called.** The agent's writes are scripted.

## Prerequisites

- Python 3.11 or newer. Standard library only (`sqlite3`); `requirements.txt` lists nothing to install.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/run_provenance_revert/provenance.py
python -m unittest discover -s examples/python/run_provenance_revert -p "test_*.py"
```

## Expected output

```
plan  CASE-5202  credit  conflict   current=15.0      restore_to=0.0
plan  CASE-5202  status  conflict   current='approved' restore_to='open'
plan  CASE-5201  credit  restore    current=25.0      restore_to=0.0
plan  CASE-5201  status  restore    current='approved' restore_to='open'
field-level would be restore
apply {'restore': 2, 'conflict': 2, 'already reverted': 0}
again {'restore': 0, 'conflict': 2, 'already reverted': 2}
row   ('CASE-5201', 'open', 0.0, '')
row   ('CASE-5202', 'approved', 15.0, '')
row   ('CASE-5203', 'approved', 0.0, '')
```

Run `run-17` changed two cases; Geetha later corrected the credit on CASE-5202 by hand. The revert restores
CASE-5201, holds back CASE-5202 for a person, and leaves CASE-5203 (written by `run-18`) alone. Seven unittest
cases cover the field-level plan, row granularity, the human correction, idempotent re-runs, two writes to one
field, reverting a revert, and atomicity of the write and its log entry.

## Limitations

Only writes made through `write_field` are tracked; side effects outside the database (emails, payments,
messages to other systems) need their own compensations. Comparing the current value with the run's value is a
simple conflict test; a later write that happens to set the same value is not detected. In production, record
the run id in the same transaction as the write, as here, or with triggers that read it from a session setting.
