# Queue visibility timeout and a slow agent step

**Author: Sandeep Belgavi**

A runnable companion to *When a Model Call Outlasts the Queue Visibility Timeout: Duplicate Agent Steps, Heartbeats and Redrive* (aicassindra.com). An offline model of an at-least-once queue (visibility timeout, receipt handles, heartbeat extensions, maxReceiveCount redrive) feeding an agent step, with an optional idempotency key on the customer reply.

## Prerequisites

- Python 3.11 or newer. Standard library only (`requirements.txt` is intentionally empty). No AWS account, no network, no model call.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

`simulate()` defaults: visibility 30 s, step 45 s, no heartbeat, maxReceiveCount 5. `python visibility.py` prints five scenarios with their traces.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Nine tests pass. Defaults: receives at t=0, 30, 60, 90, 120 s, dead letter at t=150 s, 5 replies, 225 model-seconds. Heartbeat 10 s: deleted after one receive. Heartbeat 30 s: same as defaults. Idempotency key: 1 reply, 4 suppressed, still a dead letter.

## Limitations

Whole seconds, one message, constant step time, consumers always polling. A delete with a stale receipt handle is treated as not deleting, the cautious reading of the SQS documentation. It does not call SQS and does not model the 12-hour ceiling, FIFO groups or crashes.

Views are my own and do not represent any employer, past or present.
