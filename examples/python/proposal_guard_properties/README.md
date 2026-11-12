# Property-based tests for an agent proposal guard

**Author: Sandeep Belgavi**

A runnable companion to *Property-Based Tests for the Deterministic Rules That Check Agent Proposals* (aicassindra.com). A refund guard for agent proposals (integer paise), the version that shipped first, and Hypothesis properties: conservation across sequences, approval threshold, monotonic size rejection and idempotent replay.

## Prerequisites

- Python 3.11 or newer and `pip install -r requirements.txt` (hypothesis==6.170.15) in a virtual environment. No network at test time, no model call.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Generated plans of up to twelve proposals per order. `python show_counterexample.py` prints the shrunk counterexample for the buggy guard.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Five tests pass, including one that asserts the buggy guard fails. The counterexample printed is total=1 with two one-paisa proposals, both accepted.

## Limitations

Tests the deterministic rule layer only, not the agent, and not concurrent writers to the same order. derandomize=True keeps CI reproducible but explores the same examples each run.

Views are my own and do not represent any employer, past or present.
