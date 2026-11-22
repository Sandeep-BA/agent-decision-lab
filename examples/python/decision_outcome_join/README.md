# Join agent decisions to later case outcomes

**Author: Sandeep Belgavi**

A runnable companion to *Join Agent Decisions to Later Case Outcomes Before Claiming They Help* (aicassindra.com). A seeded generator creates 1,000 synthetic help-desk cases. The agent is offered only easy cases, and 20 percent of eligible cases are held out for a person. Decision records are joined to later reopen events inside a seven-day attribution window, counted only once the window has closed. The example contrasts the naive comparison (agent cases against all person cases) with the eligible holdout, with a normal-approximation 95 percent interval for each difference.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

`generate()` with seed 20261122. The reopen probabilities are synthetic generator settings, not measurements.

## Commands

From this directory:

```
python join.py
python -m unittest -v
```

## Expected output

After every window closed: agent 41 of 479 reopened (8.6 percent), all person cases 101 of 521 (19.4 percent), eligible holdout 9 of 116 (7.8 percent). The naive difference is -10.8 points (interval -15.0 to -6.6); the holdout difference is +0.8 points (interval -4.7 to 6.3), which cannot exclude zero. Reading at day 24 without the closed-window rule counts 37 agent reopens instead of 41. 6 tests pass.

## Limitations

One decision per case, one outcome type, a normal approximation for small counts and no correction for repeated looks. It demonstrates selection bias and window censoring; it is not an experiment-analysis library.

Views are my own and do not represent any employer, past or present.
