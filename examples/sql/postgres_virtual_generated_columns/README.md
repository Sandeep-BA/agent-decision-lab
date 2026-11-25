# PostgreSQL 18 Virtual Generated Columns Compute on Read, So Plan Indexes Differently

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/databases/postgres_18_virtual_generated_columns.html (article publication pending).

Prerequisites: a disposable PostgreSQL 18 database you may create and drop tables in, CPython 3.13 and `pip install -r requirements.txt`. Copy `.env.example` and point DATABASE_URL at your own throwaway database; it contains no secrets.

From this directory:

```text
pip install -r requirements.txt
DATABASE_URL=postgresql://postgres@127.0.0.1:55441/postgres python run.py
```

`expected.json` is the recorded output from PostgreSQL 18.4 (25 statements, 0 mismatches). The script exits 1 if any statement outcome differs from its stated expectation. Tests cover failure boundaries and invariants; see the test file for each fixture.

Limitations: Outcomes were recorded against PostgreSQL 18.4 on a disposable local cluster. Later minor or major versions may change any of these behaviours; run the script against your version. No model, SDK or provider is contacted. Views are my own and do not represent any employer, past or present.
