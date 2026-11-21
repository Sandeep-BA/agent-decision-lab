# Required versus optional work in one workflow step

**Author: Sandeep Belgavi**

A runnable companion to *Separate Workflow Success From Completion of Optional Agent Checks* (aicassindra.com). Runs two required tasks and two optional agent checks for CASE-6101 with real asyncio. Putting all four in one `asyncio.TaskGroup` lets a failed optional check cancel the required work. The separated version gives optional checks their own deadline and error handling and derives the outcome with a pure function that also refuses unapproved skips and pending work at the decision point.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13.5 on Windows). Standard library only.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Durations in `DURATIONS` (80, 120, 20 and 100 ms); failures and slow tasks are chosen per call.

## Commands

From this directory:

```
python outcomes.py
python -m unittest -v
```

## Expected output

Naive TaskGroup with `tone_review` failing: both required tasks `cancelled`, outcome `failed`. Separated: `succeeded_with_warnings` with `tone_review failed`. A slow `reading_suggestion` times out at 300 ms and still gives `succeeded_with_warnings`. A skip without a reason fails; with `APPROVAL-17` it is a warning. 8 tests pass.

## Limitations

Sleeps stand in for model and tool calls. Timing margins are tens of milliseconds; a heavily loaded machine could reorder the naive case.

Views are my own and do not represent any employer, past or present.
