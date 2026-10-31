# Scheduled follow-ups across daylight-saving changes

**Author: Sandeep Belgavi**

A runnable companion to *When an Agent Schedules Work for Later* (aicassindra.com, System design). A help-desk
agent at Belgavi's Book Store promises follow-ups in the customer's own time. The example stores each one as a
wall-clock time plus an IANA zone with explicit policies for repeated and missing hours, resolves the UTC
instant with `zoneinfo`, shows the bug of converting once with the offset in force when the follow-up was
stored, and runs a fire-time check of the case before sending, with an idempotency key.

**No scheduler, database, model or network is used.** Cases are a Python set and `send` appends to a list.

## Prerequisites

- Python 3.11 or newer.
- The IANA time zone database. Windows has no system copy, so install the pinned package:
  `python -m pip install -r examples/python/scheduled_followup_dst/requirements.txt` (`tzdata==2026.1`).
  On Linux and macOS the system database is used if present.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/scheduled_followup_dst/followup.py
python -m unittest discover -s examples/python/scheduled_followup_dst -p "test_*.py"
```

## Expected output

```
london_naive           2026-11-01T13:30:00+00:00
london_resolved        2026-11-01T14:30:00+00:00
ny_repeated_earlier    2026-11-01T05:30:00+00:00
ny_repeated_later      2026-11-01T06:30:00+00:00
ny_missing_forward     2027-03-14T03:30:00-04:00
ny_missing_skip        None
runner_first           sent
runner_retry           duplicate suppressed
runner_closed          skipped: precondition no longer holds
```

A London follow-up for 14:30 on 1 November, stored on 21 October during British Summer Time, fires at 13:30
UTC (13:30 local, an hour early) if converted once, and at 14:30 UTC when resolved with the zone. New York's
01:30 on 1 November 2026 happens twice; 02:30 on 14 March 2027 does not happen. Six unittest cases check the
2026 transitions, both policies, Kolkata's lack of a transition, rejection of offsets, and the runner.

## Limitations

The runner fires exactly on time in one process. A real scheduler needs durable storage, a queue ordered by
the derived instant, recomputation when the tz database changes, and an idempotency key that survives restarts.
