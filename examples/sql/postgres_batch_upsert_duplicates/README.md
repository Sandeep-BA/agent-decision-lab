# A Batch Upsert With a Repeated Key Fails: ON CONFLICT DO UPDATE Cannot Touch a Row Twice

Author: **Sandeep Belgavi**.

Original teaching probe for https://aicassindra.com/blogs/databases/postgres_upsert_batch_duplicate_keys.html.

`run.py` seeds a small stock table for a fictional Belgavi's Book Store and runs eight statement shapes against the same rows: `INSERT ... ON CONFLICT DO UPDATE` and `DO NOTHING` with a key repeated inside one batch (for an existing and for a new key), `MERGE` with a repeated source key (matched and not matched), and two deterministic pre-aggregations (sum per key, and last value per key by sequence). It records the SQLSTATE or the resulting rows and exits 1 on any difference from `expected.json`.

Prerequisites: a disposable PostgreSQL 18 database where the `upsert_stock` table may be created and dropped, CPython 3.11+ and `pip install -r requirements.txt` (psycopg 3.2.10). Copy `.env.example`; it contains no secrets.

```text
pip install -r requirements.txt
DATABASE_URL=postgresql://postgres@127.0.0.1:55448/postgres python run.py
```

`expected.json` is the recorded output from PostgreSQL 18.4 on a disposable local cluster (0 mismatches): SQLSTATE 21000 for `DO UPDATE` and for `MERGE` with a repeated matched key, 23505 for `MERGE` inserting the same new key twice, and success for `DO NOTHING` and the pre-aggregated forms.

Limitations: one session, no concurrency; message text can change across versions, so the probe compares SQLSTATE and rows. Views are my own and do not represent any employer, past or present.
