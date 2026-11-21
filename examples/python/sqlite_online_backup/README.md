# Back up a live WAL-mode SQLite database

**Author: Sandeep Belgavi**

A runnable companion to *Back Up Live SQLite Data Without Losing Committed WAL Changes* (aicassindra.com). Creates 150 synthetic book orders in WAL mode with automatic checkpoints off, so the last 50 commits exist only in the -wal file, then compares a copy of the main file, `Connection.backup()`, `VACUUM INTO` and a paged backup while a second connection commits. Each copy is opened, integrity-checked and fingerprinted.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13.5 on Windows). Standard library only. Uses the bundled sqlite3 module (SQLite 3.49.1 here).
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Built by `build()` in a temporary directory; names Geetha, Jenya, Tanishka, Dinky and Hansini.

## Commands

From this directory:

```
python backup_wal.py
python -m unittest -v
```

## Expected output

Main-file copy: integrity `ok` but 100 rows, a different fingerprint. Backup API and VACUUM INTO: 150 rows, same fingerprint as the source. Paged backup with three concurrent commits: 153 rows, matching the source afterwards, 5 progress callbacks. 4 tests pass.

## Limitations

Single machine, small database, no crash or power-loss testing. Copy the file only when no connection is open and the WAL has been checkpointed, or use the backup API.

Views are my own and do not represent any employer, past or present.
