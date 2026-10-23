# Desired state and a level-triggered reconciler

**Author: Sandeep Belgavi**

A runnable companion to *Agents Propose Desired State, a Reconciler Converges: Level-Triggered Control
Instead of Agent-Executed Steps* (aicassindra.com, system design). The agent emits a desired state (three
read grants with an expiry) and does not call any API itself. A deterministic reconciler reads the current
state, computes the difference, and applies only the changes that close the gap. Because it is idempotent
and restartable, a crash mid-pass is recovered by the next pass, external drift is removed, and an expired
desired state revokes every grant with no separate reminder.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install.
- No API, cluster, network or credentials. The current-state store is an in-memory dict, and the clock is
  passed in. `.env.example` documents that nothing is read from the environment.

## Sample input

The desired state is built in `reconciler.demo()`: principal `contractor:erika`, read grants on `atlas`,
`orion` and `vega`, expiring 2026-10-30. `fixtures/desired.json` records the same shape. The grant keys
match the interactive lab on aicassindra.com.

## Commands

```
python reconciler.py                                   # run the default scenario
python -m unittest discover -s . -p "test_*.py"        # run the tests
```

## Expected output

`reconciler.py` prints a converged result: four changes applied across two passes (three grants added, one
drift grant removed), an unconverged gap of zero and no duplicate applies, even though pass one crashed
after one change. The tests assert convergence, that a second pass is a no-op, that one pass cannot recover
the crash (gap 3), that expiry removes every grant, and that stale reads are harmless with idempotent apply
but cause three duplicate applies without it.

## Limitations

Applies are instantaneous and the current state is read exactly; a real reconciler calls APIs that fail
individually and reads state over the network with its own consistency. The grants stand in for any
declarative end state with a time bound. The model teaches the structure — intent and progress kept apart,
idempotent keyed applies, fresh reads each pass — not production timings.
