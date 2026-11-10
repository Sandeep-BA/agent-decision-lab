# A sync handler that loses updates in a thread pool

**Author: Sandeep Belgavi**

A runnable companion to *Ray 2.60 Upgrade: Sync Serve Methods Now Run in a Thread Pool* (aicassindra.com). Reproduces the oversell that appears when a read-modify-write handler written for one event loop starts running on several threads, and the lock that fixes it.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

One copy of a book and two concurrent reservations, with a barrier that forces both reads before either write.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Three tests pass: the forced interleaving reserves the last copy twice; sequential calls are safe; the locked version reserves exactly five of five copies across forty threads.

## Limitations

Does not import or run Ray. It models the concurrency change described in the Ray 2.60.0 release notes; verify your own deployment in staging. RAY_SERVE_RUN_SYNC_IN_THREADPOOL=0 is the documented opt-out.

Views are my own and do not represent any employer, past or present.
