# Exhaustive guard coverage for one workflow state

**Author: Sandeep Belgavi**

A runnable companion to *Find Overlapping Agent Workflow Guards Before Any Action Runs* (aicassindra.com). Checks three transition guards of a refund `review` state against all eight combinations of three boolean facts (verified, over_limit, confident). Strict routing refuses any gap or overlap before the first request; priority routing takes the first match in document order, as SCXML does, and reports what it resolved silently.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13.5 on Windows). Standard library only.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Three fixtures in `FIXTURES`: `complete`, `gap` (T2 lost its "not confident" half) and `overlap` (T1 lost "verified").

## Commands

From this directory:

```
python guard_coverage.py
python -m unittest -v
```

## Expected output

`complete`: 0 gaps, 0 overlaps. `gap`: 1 gap at verified=T, over_limit=F, confident=F. `overlap`: 1 overlap at verified=F, over_limit=F, confident=T, where priority routing sends an unverified customer to `auto_refund` (reversed order sends it to `verify_identity`) and strict routing refuses the machine. A catch-all fallback closes the gap but not the overlap. 6 tests pass.

## Limitations

Boolean facts only. Numeric thresholds need their boundary values enumerated (or an SMT solver); event names, parallel states and history states from SCXML are not modelled.

Views are my own and do not represent any employer, past or present.
