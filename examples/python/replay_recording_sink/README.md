# Recording sink for capability-free replay

**Author: Sandeep Belgavi**

A runnable companion to *Replay Historical Agent Decisions Without Repeating Their Side Effects* (aicassindra.com). A replay environment receives candidate proposals through a sink that records them and has no way to perform them.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no database server, no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

Synthetic `Proposal` values built inside the tests, such as `CASE-0001` with an expected revision.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Three tests pass: a valid proposal is recorded with `executed: False`, an untyped or negative-revision proposal is rejected and not recorded, and the module exposes no effect client.

## Limitations

The sink is a small typed boundary, not a sandbox. It does not provide credential isolation or network policy; those belong in the process environment.

Views are my own and do not represent any employer, past or present.
