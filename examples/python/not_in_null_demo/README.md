# NOT IN versus NOT EXISTS with a NULL in the subquery

**Author: Sandeep Belgavi**

A runnable companion to *Why NOT IN Returns No Rows When the Subquery Contains a NULL* (aicassindra.com). Runs the same anti-join four ways against an in-memory SQLite database and shows the three-valued result of the NOT IN predicate itself.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

The `SCHEMA` string in `not_in_demo.py`: four customers and three returns, one with a NULL customer id. Run `python not_in_demo.py` to print every result.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Three tests pass. `NOT IN` returns no rows; the filtered `NOT IN`, `NOT EXISTS` and the `LEFT JOIN ... IS NULL` form all return Geetha and Dinky; `1 NOT IN (2, NULL)` evaluates to NULL.

## Limitations

Executed on SQLite only (Python standard library). PostgreSQL documents the same NOT IN rule, but plans and performance differ between engines and were not measured.

Views are my own and do not represent any employer, past or present.
