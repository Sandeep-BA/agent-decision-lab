# Change budget for agent writes

**Author: Sandeep Belgavi**

A runnable companion to *Change Budgets for Agent Writes: Capping What an Agent May Change per Window,
Staged Expansion and Automatic Halt* (aicassindra.com, agents). Per-call authorization answers whether one
change is allowed; a change budget bounds the aggregate. It counts every committed change by blast radius
(rows, distinct customers, money) and halts the agent when a cap is reached, regardless of whether each
change was individually allowed.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install.
- No network, model or credentials. The agent is a synthetic stub that emits a sequence of costed changes.
  `.env.example` documents that nothing is read from the environment.

## Sample input

Synthetic change sequences are generated in `budget.runaway_deletions(per_call_rows, calls)` and in the
tests; `fixtures/scenario.json` records the default limits. The default run is an agent whose loop deletes
120 rows on each of twenty calls against a 500-row, 50-customer budget.

## Commands

```
python budget.py                                       # run the runaway-deletion scenario
python -m unittest discover -s . -p "test_*.py"        # run the tests
```

## Expected output

`budget.py` prints that the runaway halted after committing four changes (4 x 120 = 480 rows), the fifth
projecting 600 rows over the 500 cap. The tests assert the halt happens before the cap is exceeded, that
the approve threshold (80 percent) routes to a human after three changes, that a single 1000-row statement
halts immediately while a thousand one-row changes halt only at the cap, that the customers dimension can
bind first, and that work within budget commits in full.

## Limitations

The budget counts costs supplied by the caller; in production you must measure the real blast radius before
a bulk statement commits, not after. The budget is not a substitute for authorization or for a provider
spend cap: it bounds how much the system changes, not who may call it. Staged expansion and demotion are
described in the article; this example models the enforcement, not the promotion policy.
