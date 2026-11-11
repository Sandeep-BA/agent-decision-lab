# Get-or-create on PostgreSQL with ON CONFLICT

**Author: Sandeep Belgavi**

A runnable companion to *Get-or-Create in PostgreSQL: Why ON CONFLICT DO NOTHING RETURNING Comes Back Empty* (aicassindra.com). A `get_or_create()` that inserts with `ON CONFLICT DO NOTHING RETURNING` and falls back to a SELECT in a separate statement, plus a two-connection probe that holds a conflicting insert open while each variant runs.

## Prerequisites

- Python 3.11 or newer.
- For the concurrency tests: a scratch PostgreSQL database and `pip install -r requirements.txt` (psycopg 3.2.9). Set `PG_DSN` as in `.env.example`. The tests create and drop a table named `tags`.
- Without `PG_DSN` only the SQLite tests run; the PostgreSQL tests are reported as skipped.

## Sample input

A `tags` table seeded with `poetry`; the concurrent key is `fantasy`.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
PG_DSN="host=127.0.0.1 port=5432 user=postgres dbname=scratch" python get_or_create.py
```

## Expected output

Without PG_DSN: 6 tests, 4 skipped. With PostgreSQL 18.6 (run locally on 2026-11-11): 6 pass. While another transaction holds an uncommitted `fantasy`, `DO NOTHING RETURNING` waits and returns no row, the single-statement CTE with UNION ALL also returns no row, `DO UPDATE ... RETURNING` returns the row, and `get_or_create()` returns it as existing.

## Limitations

One local PostgreSQL 18.6 run at READ COMMITTED. REPEATABLE READ and SERIALIZABLE raise serialization errors in some of these interleavings instead; they are not exercised here.

Views are my own and do not represent any employer, past or present.
