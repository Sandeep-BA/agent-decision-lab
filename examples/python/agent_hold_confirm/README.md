# Holding the last copy while a model thinks: long transaction versus expiring hold

**Author: Sandeep Belgavi**

A runnable companion to *Holding a Row Lock While the Model Thinks: Short Transactions and Expiring Holds*
(aicassindra.com, System design). The fictional Belgavi's Book Store has one signed first edition; an agent step
for CASE-5120 wants it while a website checkout tries to buy it.

- `long_transaction_step` opens a write transaction, checks stock, calls the (fake) model and then decrements,
  so the transaction stays open during the call. This is the design the article warns against.
- `hold_step` takes the copy into an expiring hold in one short transaction, calls the model with no transaction
  open, and confirms with a conditional update. `sweep` returns expired holds with the same kind of conditional
  update, so confirm and expiry cannot both succeed. A partial unique index allows one live hold per case.

**No model and no network.** The model is `time.sleep`. The database is SQLite in a temporary directory.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/agent_hold_confirm/holdconfirm.py
python -m unittest discover -s examples/python/agent_hold_confirm -p "test_*.py"
```

## Expected output

The demo starts a checkout 0.2 s into a 1.0 s model call. Waits vary by machine; on the author's Windows machine
with Python 3.13:

```
long {"agent": "swapped", "checkout": "sold_out", "checkout_wait_s": 0.9}
hold {"checkout": "sold_out", "checkout_wait_s": 0.0, "agent": "confirmed"}
```

The tests assert the shape, not exact timings: the checkout waits more than 0.6 s with the long transaction and
less than 0.2 s with the hold; an expired hold is returned by the sweeper and confirm then reports
`hold_expired`; a confirmed hold is not swept; a second live hold for the same case is rejected.

## Limitations

SQLite locks the whole database for a write transaction (`BEGIN IMMEDIATE`), which is coarser than a PostgreSQL
row lock taken by `SELECT ... FOR UPDATE`; PostgreSQL timeouts such as `idle_in_transaction_session_timeout` and
`lock_timeout` have no SQLite equivalent beyond the busy timeout. Run the same sequence against PostgreSQL before
relying on it there. The timing tests use real sleeps and may need more slack on a very slow machine.
