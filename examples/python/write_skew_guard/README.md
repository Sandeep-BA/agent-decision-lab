# Write skew between agent runs: a guarded write tool for a monthly limit

**Author: Sandeep Belgavi**

A runnable companion to *Write Skew Between Concurrent Agent Runs* (aicassindra.com, system design). The help
desk at Belgavi's Book Store may grant at most two goodwill credits per customer per month. Two threads stand in for
two agent runs: each calls the read tool, waits at a barrier until both have read, then calls the write tool.

`grant_unguarded` inserts whatever the agent decided, as a read-tool-then-insert pair does. `grant_guarded` enforces
the limit in one short `BEGIN IMMEDIATE` transaction on a quota row (`UPDATE ... WHERE used < limit RETURNING used`)
and returns a typed `limit_reached` result with a next step instead of raising.

**No model is called** and nothing leaves the machine: the database is a temporary SQLite file.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` lists nothing to install.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

Run from the repository root.

```
python examples/python/write_skew_guard/credits.py
python -m unittest discover -s examples/python/write_skew_guard -p "test_*.py"
```

## Expected output

```
unguarded credits=3 limit=2 results=['granted', 'granted']
guarded   credits=2 limit=2 results=['granted', 'limit_reached']
```

Four unittest cases: the unguarded pair breaks the limit on every repetition, the guarded tool holds it, four concurrent runs with no credits get exactly two grants, and a refusal is a result with a next step.

## Limitations

SQLite serialises writers with a database lock, so the guarded version is correct here for a simpler reason than
on PostgreSQL, where the row lock on the quota row and the re-evaluated WHERE clause do the work. Test the same
race against your real database. Every write path, including back-office screens, must use the same guard.
