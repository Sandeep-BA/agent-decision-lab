# An undo window for agent actions: schedule, cancel, claim, execute

**Author: Sandeep Belgavi**

A runnable companion to *An Undo Window Instead of Pre-Approval* (aicassindra.com, system design). Agent actions
at Belgavi's Book Store (return labels, small refunds) are scheduled with a per-kind window and run unless someone
cancels them first. `cancel` and `claim_due` are conditional `UPDATE ... WHERE state = 'scheduled' RETURNING`
statements on the same row, so exactly one of them wins. `execute` calls a fake downstream with an idempotency key
derived from the action id.

**No model and no payment provider is called.** The downstream is a table that ignores a repeated key, as a real
refund API with idempotency keys should.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` lists nothing to install.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

Run from the repository root.

```
python examples/python/undo_window/actions.py
python -m unittest discover -s examples/python/undo_window -p "test_*.py"
```

## Expected output

```
cancel return label at 1060: cancelled
claim at 1060: None
claim at 1900: 2 refund
executed with key: agent-action-2
cancel refund at 1901: {'result': 'too_late', 'state': 'done', 'next_step': 'use the compensating action for this kind of effect'}
```

Three unittest cases: 60 trials of a cancel and a claim released together, each with exactly one winner; cancel before the action is due and too_late after it is done; and a replacement executor that repeats the downstream call with the same key and produces one call.

## Limitations

On PostgreSQL add `FOR UPDATE SKIP LOCKED` to the inner SELECT so several workers do not contend for one row.
Times are integers passed in by the caller; production code should take them from the database clock. The window
lengths are illustrative. Compensation for effects that already happened is not implemented here.
