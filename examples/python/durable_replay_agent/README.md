# Durable replay agent

**Author: Sandeep Belgavi**

A runnable model of the replay mechanism described in *Durable Execution for Agent
Workflows* (aicassindra.com, agents). A procurement workflow drafts an order through a
"model" activity, waits for approval above a threshold, places the order and notifies. The
`Replayer` records every activity result in a history; resuming the workflow on a fresh
worker replays that history so that completed activities, including the model call, are
**never executed again**. A reordered activity raises a non-determinism error; a patch
marker versions the change so old histories replay the old path and new runs take the new
one.

The engine API is deliberately minimal and SDK-neutral; it is not Temporal or Restate, it
illustrates what they do.

## Prerequisites

- Python 3.11 or newer. Standard library only.
- No network, no model provider, no credentials. The model call is a deterministic stub
  that returns a synthetic proposal; `.env.example` documents the one optional variable.

## Commands

From the repository root:

```sh
python examples/python/durable_replay_agent/replay.py --demo
python -m unittest discover -s examples/python/durable_replay_agent -p "test_*.py"
```

## Sample input and expected output

`fixtures/history_p204.json` is a recorded history for run P-204: the draft activity
completed with supplier B for 7,200 and the run blocked waiting for approval (the blocked
wait is recorded, as the workflow task that evaluated it would be). `--demo` resumes it on
a worker running the newer workflow code with a patch marker:

```
replay P-204 from 2 recorded entries, approval=granted
  draft_order: replayed (model not called)
  compliance_check: skipped (patch compliance-check-2026-10 absent from this history)
  place_order: executed live with idempotency key P-204:place_order
  notify: executed live
result=ORD-7200-B live_activities=2 model_calls=0
new run P-205 on the same code: patch recorded, compliance_check executed
```

## Tests

`test_replay.py` checks: replay returns recorded results without calling activities; a
reordered activity raises `NonDeterministic`; the patch marker takes the old path on an old
history and the new path on a new run; the effecting activity carries the workflow id as
its idempotency key; and the recorded history is identical after a resume.

## Limitations

- Single-threaded, in-memory; no timers, no signals beyond a pre-recorded approval, no
  retries or heartbeats.
- The model activity is a stub. A real one would call a provider inside the activity and
  must still never run inside workflow code.
- Teaching model only; use a durable execution engine for production.
