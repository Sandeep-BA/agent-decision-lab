# Preserve PostgreSQL array subscripts

Author: **Sandeep Belgavi**.

Companion for https://aicassindra.com/blogs/databases/postgres_array_ordinality_subscripts.html (publication pending).

Prerequisites: PostgreSQL 18.4 (local test target). Use a disposable database and a matching `psql`, or CPython with `psycopg[binary]==3.2.10`. All fixtures are synthetic. No model or remote service is contacted.

```text
psql -X -v ON_ERROR_STOP=1 -f example.sql
```

Alternatively install the pinned requirements, set `DATABASE_URL` to your disposable database outside source, and run `python run.py`. The `.env.example` contains no password; it is not loaded automatically.

Expected rows are `(0,10), (1,NULL), (2,30)`. The final result begins `PASS:`. Assertions cover zero-based and negative bounds, ordinality mismatch, empty/null distinction, shape-sensitive equality and rejection of unsupported list shapes. Every temporary table is inside a transaction rolled back at the end.

This tests SQL array behavior only. It does not prove a particular application's driver preserves array bounds when converting to a host-language list. Views are my own and do not represent any employer, past or present.
