# Agent writes without lost updates: version checks and coupled-field merges

**Author: Sandeep Belgavi**

A runnable companion to *Agents and Lost Updates: Version Checks, Re-Planning on Conflict and Field Merges
When Think Time Is Seconds* (aicassindra.com, System design). An agent reads a support ticket at version 7,
reasons for a while, and writes. Meanwhile a person raises the priority to P1 and adds a note (version 8).
The example compares three write strategies with that fixed interleaving.

## Prerequisites

- Python 3.11 or newer. Standard library only (`sqlite3`, `json`); `requirements.txt` is intentionally empty.
- No network, no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

`seed()` inserts ticket T-4471 at version 7: status open, priority P3, empty note and summary.
`person_escalates()` is the concurrent human edit.

## Commands

```
python writes.py                                       # print the three strategies
python -m unittest discover -s . -p "test_*.py"        # run the tests
```

## Expected output

```
unconditional "ok" null 9 {"status": "resolved", "priority": "P3", "note": "", "summary": "Duplicate charge refunded"}
status_and_summary "conflict" ["note", "priority"] 8 {"status": "open", "priority": "P1", "note": "Customer is a hospital", "summary": ""}
summary_only "ok" null 9 {"status": "open", "priority": "P1", "note": "Customer is a hospital", "summary": "Duplicate charge refunded"}
```

The unconditional write silently undoes the escalation. Changing status conflicts because status and priority
are declared as a coupled group, and the conflict result names the fields that changed since the read so the
agent can re-plan. Writing only the summary merges and keeps both changes. A fourth test shows that the final
`UPDATE ... WHERE version = ?` rejects a write when another writer commits between the check and the update.

## Limitations

One ticket, one interleaving, SQLite. A real service needs the same guard on every write path, including
child tables, and a re-plan budget with escalation in the agent loop, which this example does not include.
