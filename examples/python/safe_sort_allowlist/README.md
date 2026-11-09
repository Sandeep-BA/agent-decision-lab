# Allowlisted SQL sorting

**Author: Sandeep Belgavi**

A runnable companion to *Safe Dynamic SQL Sorting Starts With an Explicit Column Allowlist* (aicassindra.com). Public sort options map to SQL fragments owned by the application; the filter value stays bound.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no database server, no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

Three synthetic books loaded into an in-memory SQLite table, two sharing a page count.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Three tests pass: exact id order for every key and direction including the tie, bound-value filtering, and rejection of four unsafe inputs before any database call.

## Limitations

SQLite only. No authentication, web layer or other database dialect is exercised.

Views are my own and do not represent any employer, past or present.
