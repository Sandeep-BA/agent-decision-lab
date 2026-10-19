# Agent outbox journal

**Author: Sandeep Belgavi**

A runnable model of the design in *Agent Tool Effects Through a Transactional Outbox*
(aicassindra.com, system design). One agent run issues a refund through a tool handler
that writes the business row, the step journal row and the outbox row in **one SQLite
transaction**; a relay publishes outbox rows at least once; a consumer deduplicates on the
outbox id. Fault injection lets you crash the handler or the relay at chosen points and
see which invariant holds.

## Prerequisites

- Python 3.11 or newer. Standard library only (`sqlite3`, `json`, `argparse`, `unittest`).
- No network, no model provider, no credentials. `.env.example` lists the one optional
  variable (a database path); copy it to `.env` only if you want a file-backed database.

## Commands

From the repository root:

```sh
python examples/python/agent_outbox_journal/outbox_journal.py --scenario clean
python examples/python/agent_outbox_journal/outbox_journal.py --scenario crash-after-commit --no-step-key --no-resume
python examples/python/agent_outbox_journal/outbox_journal.py --scenario relay-crash --no-dedup
python -m unittest discover -s examples/python/agent_outbox_journal -p "test_*.py"
```

Scenarios: `clean`, `crash-before-commit`, `crash-after-commit`, `relay-crash`,
`agent-retry`. Flags: `--no-atomic`, `--no-step-key`, `--no-dedup`, `--mark-first`,
`--no-resume`.

## Sample input and expected output

`fixtures/run_r91.json` is a synthetic three-step plan for order 7731 (lookup, refund of
40, notify). Expected output of the first command:

```
scenario=clean atomic=True step_key=True dedup=True relay=publish_then_mark resume=True
refunds=1 journal_steps=2 outbox_rows=1 deliveries=1 ledger_entries=1
invariants: duplicate_refunds=0 lost_events=0 duplicate_postings=0
```

With `--scenario crash-after-commit --no-step-key --no-resume`, `refunds=2` and
`duplicate_refunds=1`: the restarted run repeats the effect because neither the journal
(resume is off) nor a step key lets the repeated call find the earlier result. With
`--scenario relay-crash --no-dedup`, `deliveries=2` and `duplicate_postings=1`.

## Tests

`test_outbox_journal.py` runs every scenario against the invariants described in the
guide: exactly one refund, every refund told to the ledger exactly once, with each
safeguard switched on; and the specific violation each switched-off safeguard produces.

## Limitations

- SQLite stands in for PostgreSQL; `FOR UPDATE SKIP LOCKED` is not modelled and the relay
  is single-threaded.
- Crash points are explicit calls, not timing. The broker is an in-memory list that never
  reorders.
- The agent is a fixed policy that retries a call it saw no answer for. No model is called.
- This is a teaching model of the mechanics, not a production library.
