# Advisory locks behind a transaction pooler (model)

**Author: Sandeep Belgavi**

A runnable companion to *PostgreSQL Session Advisory Locks Break Behind Transaction Pooling* (aicassindra.com). A model of the documented semantics: session-level advisory locks are re-entrant and counted per backend and survive transaction end; transaction-level locks end at commit; a transaction-mode pool hands each transaction the longest-idle backend; a session pool pins a client to one backend and runs DISCARD ALL on release. Two synthetic workers, Tanishka and Jenya, run the same nightly job.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

The statement sequences in `run_session_lock()` and `run_xact_lock()`.

## Commands

From this directory:

```
python pool_model.py
python -m unittest -v
```

## Expected output

Transaction pooling with session locks: backends S1, S2, S1, S2, S1; both workers are told they hold lock 42, Tanishka's unlock on S2 returns false, and one hold on S1 is left behind. Session pooling: Jenya is refused and nothing leaks. Transaction-level lock under transaction pooling: true, false, then true after commit, nothing left. 5 tests pass.

## Limitations

A model, not a run against PostgreSQL or PgBouncer. It encodes the rules cited in the article; check them against your own versions with pg_locks before relying on them.

Views are my own and do not represent any employer, past or present.
