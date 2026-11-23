# Orchestrator-owned fan-in for parallel agent subtasks

**Author: Sandeep Belgavi**

A runnable companion to *Join Parallel Agent Subtasks With a Quorum and a Deadline, Not Wait-for-All* (aicassindra.com). Four reviewer subtasks check a refund on a help-desk case; one fails, one is slow and dissents. The orchestrator applies `all`, `quorum` (k agreeing) or `first_valid` with a deadline, lists late subtasks for cancellation, records exactly which results the decision used and supports a required veto check.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

`SUBTASKS` in `join.py`: policy-reader approves at 0.8 s, payment-check fails at 1.2 s, order-history approves at 2.5 s, fraud-signals rejects at 9.0 s (simulated time).

## Commands

From this directory:

```
python join.py
python -m unittest -v
```

## Expected output

all/12 s: escalate at 9.0 s (a subtask failed). all/5 s: escalate at the deadline, cancel fraud-signals. quorum k=2: approve at 2.5 s using policy-reader and order-history, fraud-signals ignored. quorum k=3: escalate at 5.0 s. first_valid: approve at 0.8 s. With fraud-signals required: reject at 9.0 s (deadline 12 s) or escalate at 5.0 s. 8 tests pass.

## Limitations

Simulated time and fixed verdicts; there is no model, no real cancellation and no retry policy. The point is the decision record, not the reviewers.

Views are my own and do not represent any employer, past or present.
