# Detecting stuck agent loops

**Author: Sandeep Belgavi**

A runnable companion to *Detecting Stuck Agent Loops* (aicassindra.com, Agents). A returns agent at Belgavi's
Book Store records one tool call per step. This example replays recorded synthetic runs through a detector that
fingerprints normalised calls and results over a window and tracks a task-state progress signal: an exact
repeat, an A-B oscillation, a paraphrase loop whose arguments change while the result does not, a healthy run,
legitimate polling, and an exact repeat whose JSON arguments arrive in a different key order.

**No model, agent framework or tool is called.** Runs are lists of `(tool, args, result, state)` tuples.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` lists nothing to install.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/stuck_loop_detector/detector.py
python -m unittest discover -s examples/python/stuck_loop_detector -p "test_*.py"
```

## Expected output

```
exact                  3  same call and result 3 times
oscillation            5  same call and result 3 times
paraphrase             3  same result 3 times without progress
polling                8  finished
healthy                5  finished
reordered_args         3  same call and result 3 times
polling_not_exempt     3  same call and result 3 times
budget_only_exact     30  step budget
```

Each loop shape is stopped within five steps; the healthy and polling runs finish. Without the polling
exemption the polling run is stopped as a loop, and with no detector only the 30-step budget ends the exact
repeat. Volatile result fields (`request_id`, `fetched_at`, `latency_ms`) are stripped before hashing, which
is why the exact loop and the polling run still look repetitive. Eight unittest cases cover the shapes, the
exemption, normalisation, the budget, the progress-only path and counter resets.

## Limitations

Real runs need a domain definition of progress; here it is a small dict that changes when the case status
changes. Thresholds were chosen for these fixtures. Replay your own recorded runs through the detector, and
label a sample of its stops, before enforcing it in production.
