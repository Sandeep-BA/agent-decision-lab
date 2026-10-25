# Agent paging: offset drift versus keyset cursors

**Author: Sandeep Belgavi**

A runnable companion to *Letting an Agent Page Through an Existing API: Offset Drift, Keyset Cursors,
Snapshot Reads and When to Return an Aggregate Instead* (aicassindra.com, System design). An agent reads a
list one page at a time and reasons between pages, so new items arrive and read items are closed while it
scans. Offset paging returns some items twice and skips others; a keyset cursor does not. The example also
contains the agent-facing tool: a keyset page over `(created_at, id)` with an HMAC-signed opaque cursor and
a page-size cap.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no database, no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

- `scan()` builds a synthetic newest-first list of 1,000 ids with timed inserts and closes.
- `fixtures/tickets.json` holds five tickets, two pairs of which share a `created_at`, to exercise the
  tie-breaking id in the keyset predicate.

## Commands

```
python paging.py                                       # print the four scenario results
python -m unittest discover -s . -p "test_*.py"        # run the tests
```

## Expected output

`python paging.py` prints, for the defaults (1,000 items, pages of 50, 20 s between pages, 3 inserts and
1 close per minute), 21 pages and 1,014 items returned with 14 duplicates for offset paging and 1,000 items
with no duplicates for keyset paging. With 1 insert and 4 closes per minute, offset paging misses 19 items
and keyset paging misses none. The tests assert those figures, that a keyset walk over the fixture returns
every ticket exactly once despite timestamp ties, that an edited cursor is rejected, and that the page size
is capped at 100.

## Limitations

The model applies writes at exact times and orders by one increasing id; real lists sort by a timestamp plus
a tie-breaker and receive bursty writes. Closes are modelled as items the reader has already passed, which is
the case that makes offset paging skip items. Keyset paging does not freeze rows whose sort key changes during
a scan; use a snapshot for that. The signing secret is an example value. Figures are from this synthetic model,
not from a production system.
