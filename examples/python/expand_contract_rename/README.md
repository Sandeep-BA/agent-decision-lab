# Expand-contract rename with agent clients

**Author: Sandeep Belgavi**

A runnable companion to *Renaming a Column That Agents Still Use* (aicassindra.com, System design). Belgavi's
Book Store moves `returns.refund_amount` (pounds) to `refund_amount_minor` (pence). The example runs the phases
on SQLite: expand with sync triggers and an old-write log, backfill in batches, agent tools v1 (old column) and
v2 (new column) working side by side, a scanner that finds the old name in synthetic prompts, tool schemas,
eval fixtures and memory notes under `fixtures/`, a contract gate, and the drop.

**No model or network is used.** SQLite stands in for the production database; its AFTER triggers play the part
of the PostgreSQL BEFORE trigger shown in the article. Because an AFTER trigger syncs with a nested UPDATE, the
old-column trigger needs a guard so it does not log the nested write; the tests check that guard.

## Prerequisites

- Python 3.11 or newer with the bundled `sqlite3` (SQLite 3.35 or newer for `DROP COLUMN`). Standard library
  only; `requirements.txt` is intentionally empty.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/expand_contract_rename/migration.py
python -m unittest discover -s examples/python/expand_contract_rename -p "test_*.py"
```

## Expected output

```
batches                              3
half_filled                          0
old_tool_write_seen_by_new_reader    {'case_id': 'CASE-6003', 'refund_amount_minor': 1234}
new_tool_write_seen_by_old_reader    {'case_id': 'CASE-6004', 'refund_amount': 9.99}
contract_allowed_before_cleanup      False
contract_allowed_after_cleanup       True
columns_after_contract               ['id', 'case_id', 'refund_amount_minor']
references {'evals/case_6003.json': 2, 'memory/session_notes.jsonl': 1, 'prompts/refund_agent.md': 2, 'tools/get_refund.json': 1}
```

Seven unittest cases check batching, both writers staying in step, inserts through either column, that only
old-column writes are logged, the scanner, the contract gate and the drop.

## Limitations

One process and twelve rows. A production backfill needs throttling and replica-lag checks, the trigger must
be tested under concurrent writers, and whether to rewrite or annotate stored memory is a policy decision that
the scanner only informs.
