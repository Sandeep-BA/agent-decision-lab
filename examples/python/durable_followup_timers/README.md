# Durable follow-up timers for agent waits

**Author: Sandeep Belgavi**

A runnable companion to *Schedule Agent Follow-Ups as Durable Timers, Not Sleeps Inside the Loop* (aicassindra.com). An agent asks a customer a question on a help-desk case and must follow up if no reply arrives. The example compares an in-process wait, which a restart forgets, with a timer row in SQLite: a deterministic due-time rule (two days later at 09:00 UTC, moved off weekends), a compare-and-set claim so two workers cannot both fire a timer, cancellation by a customer reply that arrives first, and an outbox insert that a retried fire cannot duplicate.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Cases CASE-4101 to CASE-4104 built in `run()`; Jenya and Geetha reply on two of them.

## Commands

From this directory:

```
python timers.py
python -m unittest -v
```

## Expected output

All three questions asked on Friday 20 November 2026 are due Monday 23 November at 09:00 UTC. The in-process wait sends nothing after a restart at 20 hours. Durable timers: CASE-4102 is cancelled by the reply, worker-a claims CASE-4101 and CASE-4103, worker-b claims nothing, the late reply on CASE-4103 loses the race, and the outbox holds exactly two follow-ups after a retried fire. 6 tests pass.

## Limitations

SQLite in memory with one process; a production table needs an index on (state, due_at), a claim lease so a crashed worker's claim can be retried, and a business-calendar rule rather than weekends only. The late-reply race is shown, not solved: the sender should re-check the case before the message leaves.

Views are my own and do not represent any employer, past or present.
