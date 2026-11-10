# Nightly reminder job with a delegated drafting step

**Author: Sandeep Belgavi**

A runnable companion to *Moving a Nightly Batch Job Onto an Agent Without Losing Its Deterministic Core* (aicassindra.com). Selection, idempotency keys, draft acceptance rules, the send ledger and the checkpoint stay deterministic; only the message wording comes from a drafter callable.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

`fixture()` in `nightly.py`: five synthetic book loans for Belgavi's Book Store, three of them overdue on 10 November 2026.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Five tests pass: a crash after a send and a lost checkpoint both re-run without a duplicate; a draft that promises a refund goes to review; a drafter timeout goes to retry while the run continues.

## Limitations

The drafter in the tests is a local function, not a model. The outbox is an in-memory list; a real job needs a durable ledger written in the same transaction as the send record.

Views are my own and do not represent any employer, past or present.
