# A workflow map step: fail fast, collect, bounded workers and resume

**Author: Sandeep Belgavi**

A runnable companion to *Map Steps Over Lists in Agent Workflows: Fail Fast or Collect, Bounded Workers and Resume Without Redoing Items* (aicassindra.com). A discrete-time model of a step that runs one child per list item, at most N at a time, under a fail-fast or collect policy, with an optional per-item checkpoint, a crash and a resume. It mirrors the documented shape of the experimental ParallelWorkers node in ADK Java 1.14.0 (results in input order; a failed item cancels the others; an item that asks for input stops queued items) but does not use ADK.

## Prerequisites

- Python 3.11 or newer. Standard library only.
- `.env.example` documents that nothing secret is read from the environment. No API keys, no network calls beyond loopback.

## Sample input

Eight synthetic help-desk cases CASE-5101..CASE-5108 with durations 4, 7, 3, 9, 5, 6, 2 and 8 seconds (`CASES` in map_step.py).

## Commands

From this directory:

```
python map_step.py
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

3 workers: completed at t=19 s. 1 worker: 44 s. CASE-5104 fails under fail_fast: failed at 12 s, CASE-5106 and CASE-5108 cancelled, 6 s of work wasted. Under collect: 7 ok and 1 error at 19 s. Crash at 12 s: resume with checkpoints starts 2 items and finishes at 20 s (10 starts in total); without checkpoints it starts all 8 again and finishes at 31 s (16 starts). CASE-5103 asks for input: paused at 7 s with 5 items not started. 9 tests pass.

## Limitations

Whole seconds, fixed durations, no retries, no partial results inside an item and no real engine. Use it to reason about policies, then measure your own item latencies.

Views are my own and do not represent any employer, past or present.
