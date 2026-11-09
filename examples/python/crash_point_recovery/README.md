# Crash-point recovery with an independent oracle

**Author: Sandeep Belgavi**

A runnable companion to *Kill an Agent Run at Every Step Before Trusting Its Recovery* (aicassindra.com). A worker writes a refund note for a Belgavi's Book Store help-desk case and is killed with `os._exit` at each durable boundary. A new worker recovers against the same stores.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no database server, no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

One synthetic case, `CASE-0017`, created by the worker in a throwaway SQLite file next to the tests.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Three tests pass. Five crash positions (`before_plan`, `after_plan`, `before_effect`, `after_effect`, `after_complete`) each end with exactly one effect row and a completed task. The unsafe mode, which mints a new operation id per attempt, leaves two effect rows after a crash at `after_effect`, which is the failure the safe path prevents. Reusing an operation id with a changed payload raises `ValueError`.

## Limitations

SQLite stands in for the effect service. This does not test a remote provider, power loss, concurrent workers or a production adapter. Five positions do not cover all distributed interleavings.

Views are my own and do not represent any employer, past or present.
