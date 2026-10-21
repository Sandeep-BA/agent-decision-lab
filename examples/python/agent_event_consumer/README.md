# Agent step inside an existing event consumer

**Author: Sandeep Belgavi**

A runnable companion to *Putting an Agent Step Inside an Existing Event Consumer: Per-Key Ordering,
Model Rate Limits, Poison Events and Effects That Survive Redelivery* (aicassindra.com, system design).
A synthetic stream of payment disputes, three partitions of eight events, goes through a consumer whose
only non-deterministic step is a (fake) model decision:

- a 429 from the model pauses **only** the affected partition until Retry-After;
- an event whose decision never validates is parked after three attempts, and the later events of the
  same key are parked with it, so a key is never applied out of order;
- offsets are committed every 5 s (auto-commit style) or after every event;
- effects carry a key built from topic, partition and offset, checked before the model is called, so a
  crash that redelivers finished events applies nothing twice and spends no extra model calls.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install.
- No broker, network, model provider or credentials. The model is `FakeModel`: it allows a fixed number
  of calls per 10 s window on a simulated clock and rejects the poison payload. `.env.example` documents
  that nothing is read from the environment.

## Sample input

`fixtures/disputes.json`: topic `disputes`, three partitions, keys `acct-a` to `acct-i`. Partition 1,
offset 2 (`acct-e`) is a poison event. Keys and partitions match the interactive lab on aicassindra.com.

## Commands

From the repository root:

```sh
python examples/python/agent_event_consumer/consumer.py
python examples/python/agent_event_consumer/consumer.py --crash-at 25
python examples/python/agent_event_consumer/consumer.py --crash-at 25 --commit each
python examples/python/agent_event_consumer/consumer.py --per-window 30
python -m unittest discover -s examples/python/agent_event_consumer -p "test_*.py"
```

## Expected output (verified with Python 3.13)

Default run (6 calls per window, no crash):

```
finished_at: 35.0
effects_applied: 21
model_calls: 24
rate_limited: 8
partition_pauses: 10
redelivered: 0
committed: {0: 8, 1: 8, 2: 8}
parked: (1, 2, 'acct-e', 'decision does not match the schema: missing field action')
parked: (1, 5, 'acct-e', 'earlier event of this key is parked')
parked: (1, 7, 'acct-e', 'earlier event of this key is parked')
```

With `--crash-at 25` the output is the same except `redelivered: 3`: three finished events after the last
commit are delivered again and recognised by their effect keys. With `--commit each` it is `redelivered: 0`.
The 24 model calls are 21 events plus three attempts on the poison event.

## Tests

`test_consumer.py` (9 tests): effects follow offset order within every key; the poison event and the later
`acct-e` events are parked and 21 effects are applied; no window ever exceeds its call limit; a higher limit
finishes sooner; a crash redelivers events without duplicating effects; a write path without effect keys
does duplicate them; committing after every event leaves nothing to redeliver; retrying a poison event for
ever blocks only its own partition; a decision with a disallowed action is invalid.

## Limitations

- The driver processes each partition strictly in order to stay short. The article and the interactive lab
  cover parallelism across keys within a partition, which needs per-key in-flight tracking and a commit of
  the contiguous finished prefix.
- One consumer, no rebalances other than the simulated crash, and a fixed-window rate limiter. Real
  providers report limits in different ways; read their Retry-After or rate-limit headers.
- The effect store is a dictionary. In a real system the effect key needs a unique constraint in the same
  transaction as the effect.
- Nothing here measures model quality: the fake model's decisions are fixed in the fixture.
