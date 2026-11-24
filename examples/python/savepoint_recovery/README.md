# Recover a Failed SQL Step Without Committing the Outer Transaction

Author: **Sandeep Belgavi**. Original explanation, code and synthetic fixtures.

Use savepoint rollback to recover transaction usability while preserving the distinction between release and durable commit.

Article destination (publication pending): https://aicassindra.com/blogs/databases/postgres_savepoint_outer_transaction_recovery.html

## Prerequisites

CPython 3.13.5. No third-party dependencies; requirements.txt intentionally contains no packages.

## Run from this directory

```text
python example.py
python -m unittest test_example -v
```

Input: `sample-input.json`. Expected output: `expected-output.json`. Tests include negative outcomes, state preservation and boundary cases. All fixtures are synthetic; no provider call occurs.

## Limits

Offline state machine only. PostgreSQL SQL supplied for a separate integration run; no server run claimed. The model deliberately refuses commit while aborted and does not implement the PostgreSQL wire protocol, WAL, locks or cursors.

Views are my own and do not represent any employer, past or present.

## Primary references

- [PostgreSQL 18 SAVEPOINT](https://www.postgresql.org/docs/18/sql-savepoint.html)
- [PostgreSQL 18 ROLLBACK TO SAVEPOINT](https://www.postgresql.org/docs/18/sql-rollback-to.html)
