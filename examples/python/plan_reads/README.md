# Revalidate Every Read Dependency Before Applying an Agent Plan

Author: **Sandeep Belgavi**. Original explanation, code and synthetic fixtures.

Keep planning outside transactions, then compare all recorded dependency versions atomically with the proposed state change.

Article destination (publication pending): https://aicassindra.com/blogs/system_design/agent_plan_read_dependency_validation.html

## Prerequisites

CPython 3.13.5. No third-party dependencies; requirements.txt intentionally contains no packages.

## Run from this directory

```text
python example.py
python -m unittest test_example -v
```

Input: `sample-input.json`. Expected output: `expected-output.json`. Tests include negative outcomes, state preservation and boundary cases. All fixtures are synthetic; no provider call occurs.

## Limits

Single-process in-memory lock and trusted evidence only; no database, distributed transaction or predicate-read protection.

Views are my own and do not represent any employer, past or present.

## Primary references

- [PostgreSQL 18 transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html)
