# Message-thread replay planner

**Author: Sandeep Belgavi**

A runnable companion to *Claude Message Threads: Build the Replay Path Before the 404* (aicassindra.com). A pure function chooses create or continue, and a table maps documented outcomes to the next step.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no database server, no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

Synthetic messages for help-desk case `CASE-0042`, written in the tests.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Three tests pass: create and continue request shapes, no mutation of stored history, and the recovery table for `thread_not_found`, a non-thread 404, `thread_fingerprint_mismatch` and a refusal.

## Limitations

No API call is made, so service retention, billing and model behaviour are untested. The feature is in beta; re-read the documentation before relying on these request shapes.

Views are my own and do not represent any employer, past or present.
