# A previewed bulk change instead of a per-row agent loop

**Author: Sandeep Belgavi**

A runnable companion to *Bulk Changes From an Agent: A Previewed Set-Based Job Instead of a Thousand Tool
Calls* (aicassindra.com, System design). An agent is asked to put a publisher's older paperbacks on
clearance. Instead of one `update_price` call per book, it proposes a declarative specification; the service
previews it as a manifest of `(id, version)` pairs with a SHA-256 hash, the approver approves that hash,
and a batch job applies it, skipping rows changed since the preview and resuming after an interruption.

**No model or network is called.** The proposal is a fixed specification and the catalogue is an in-memory
SQLite database of 60 synthetic books.

## Prerequisites

- Python 3.11 or newer. Standard library only (`sqlite3`); `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/agent_bulk_change_job/bulkjob.py
python -m unittest discover -s examples/python/agent_bulk_change_job -p "test_*.py"
```

## Expected output

```
first preview   : 10 rows, hash f8823236a744
revised preview : 7 rows, hash 2f2be327ab0d (books already at 40% excluded)
run, interrupted: applied 4, skipped ['BK-4015'], batches 1
resume          : applied 1, skipped ['BK-4053'], batches 1
per-row loop would have made 7 write tool calls; this flow made 2 proposals
```

The two skipped books were repriced by a merchandiser after the preview, so the job leaves them alone and
reports them. Six unittest cases check the counts, that preview writes nothing, that filters outside the
allow-list are refused, that an approval for another manifest is refused, the stale-row skip, and that
resuming never applies a row twice.

## Limitations

One table, equality and range filters only, and no concurrency between job workers. A real service needs
an expiry on unapproved manifests, an approver identity on the approval, and a report of skipped rows to a
person.
