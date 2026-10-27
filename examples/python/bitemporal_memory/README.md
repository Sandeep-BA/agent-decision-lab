# Bitemporal agent memory: valid time, record time, corrections, conflicts and erasure

**Author: Sandeep Belgavi**

A runnable companion to *Bitemporal Agent Memory: Recording When a Fact Was True Separately From When the
Agent Learned It* (aicassindra.com, Agents). A customer's shipping address changed on 3 October and the help
desk learned it on 10 October, in CASE-5120. The memory keeps both time axes, so it can answer what is true
now, what applied on a past date as we now know it, and what the agent believed at the time.

**No model is called.** In a real agent the model proposes a fact, its valid-from date and its source; the
deterministic functions in `memory.py` open and close the intervals. Facts come from `fixtures/events.json`.

## Prerequisites

- Python 3.11 or newer with the bundled `sqlite3`. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/bitemporal_memory/memory.py
python -m unittest discover -s examples/python/bitemporal_memory -p "test_*.py"
```

## Expected output

- now: `12 Lake Road` (source CASE-5120)
- the address that applied to an order of 5 October, as known now: `12 Lake Road`
- what the agent believed on 7 October: `4 Hill Street` (source account signup)
- 3 rows: the original belief with its record interval closed on 10 October, the corrected history of the old
  address ending 3 October, and the new address.

The tests also cover a correction (same valid period, new record row), two conflicting sources that stay
visible together, and an erasure that deletes all three rows.

## Limitations

Dates are ISO strings without time zones, there is no index or exclusion constraint, and conflicts are only
surfaced, not resolved. The guide shows the PostgreSQL range-type version with an exclusion constraint.
