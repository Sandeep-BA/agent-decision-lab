# Simulated-user evaluation: personas, end-state checks, pass^k and failure attribution

**Author: Sandeep Belgavi**

A runnable companion to *Evaluating a Conversational Agent With a Simulated User: Goal Scripts, Stop Rules,
Simulator Drift and Blaming the Right Side* (aicassindra.com, Agents). A small booking agent changes flight
dates; a simulated user holds a goal script with private facts and reveals them according to a persona. Each
conversation is judged by the end state of the booking store, success over repeated trials is summarised as
pass^1 and pass^k (the estimator from the tau-bench paper, arXiv 2406.12045), and every failure is attributed
either to the agent or to the simulator by checking whether the simulator stated only facts from its script.

**No model is called.** The agent and the simulator are deterministic rule programs with a seeded random
source. They stand in for LLM-backed components so that the evaluation logic can be tested exactly.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Sample input

`fixtures/tasks.json` holds four goal scripts: two valid date changes, one inside the 24-hour no-change window,
and one with a wrong surname. The booking store is the `BOOKINGS` constant in `simeval.py`.

## Commands

```
python simeval.py                                      # one JSON line per persona and agent
python -m unittest discover -s . -p "test_*.py"        # run the tests
```

## Expected output

Four trials per task. The agent with `careful=False` skips the 24-hour check when the new date arrives in the
user's first message.

- `waits` persona (answers only what is asked): both agents score pass^1 1.0. The bug is invisible.
- `detailed` persona (volunteers everything): the buggy agent fails all four trials of the late booking,
  pass^1 0.75; the failures are attributed to the agent.
- `mixed` persona (volunteers each fact with probability 0.5): the buggy agent scores pass^1 0.938 but
  pass^4 0.75, because it is right on the late booking only some of the time.
- Careful agent with a simulator that invents a different date 25 percent of the time: pass^1 0.875 and
  pass^4 0.75, and both failures are attributed to the simulator, not the agent.

## Limitations

Real simulators are language models; their drift is subtler than an invented date, and attribution needs a
rubric check on the transcript, not only a fact comparison. Four tasks and four trials are far too few for a
real decision. The booking store and policy are invented for the example.
