# A Failed CREATE INDEX CONCURRENTLY Can Leave an Invalid Index That Still Takes Writes

Author: **Sandeep Belgavi**.

Original teaching probe for https://aicassindra.com/blogs/databases/postgres_failed_concurrent_index_invalid.html.

`run.py` creates a table for a fictional Belgavi's Book Store case log and records, on PostgreSQL 18:

1. a `CREATE UNIQUE INDEX CONCURRENTLY` that fails on existing duplicates (left `indisvalid=false`, `indisready=false`, 0 bytes, no growth on insert);
2. a `REINDEX INDEX CONCURRENTLY` of that index failing the same way and leaving a `_ccnew` index;
3. a `CREATE INDEX CONCURRENTLY` cancelled while in the phase `waiting for old snapshots`, forced by an open REPEATABLE READ transaction (left `indisvalid=false`, `indisready=true`, the index keeps growing on INSERT and the planner does not use it);
4. the same wait ended by `lock_timeout` (2 s) instead of a cancel, which leaves the same ready-but-invalid kind of index;
5. the listing query and cleanup with `DROP INDEX CONCURRENTLY`.

Prerequisites: a disposable PostgreSQL 18 database where you may create and drop the `cic_orders` table, CPython 3.11+ and `pip install -r requirements.txt`. Copy `.env.example`; it contains no secrets.

```text
pip install -r requirements.txt
DATABASE_URL=postgresql://postgres@127.0.0.1:55447/postgres python run.py
```

`expected.json` is the recorded output from PostgreSQL 18.4 on a disposable local cluster (0 mismatches). The script exits 1 if any outcome differs from its expectation.

Limitations: outcomes depend on the failure phase; other phases (for example a cancel during the initial build) are not covered. Later versions may differ; run it against yours. Views are my own and do not represent any employer, past or present.
