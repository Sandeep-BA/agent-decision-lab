# Shared versus isolated state in agent evaluation trials

**Author: Sandeep Belgavi**

A runnable companion to *Isolating Agent Evaluation Trials: Fresh State per Trial, Leak Detection and
Parallel Interference* (aicassindra.com, Agents). A scripted refund agent for a book shop has a budget of
three tool calls, and the task (refund the damaged hardcover in CASE-4417) needs four. Run against a fresh
copy of a template database, it fails every trial. Run three times against one shared database, it "passes"
the second and third trials, because the first trial left an approved return behind. A start-state
fingerprint marks those trials invalid.

**No model or network is called.** The agent is a scripted function and the fixtures are a synthetic SQLite
template created in a temporary directory.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/eval_trial_isolation/isolation.py
python -m unittest discover -s examples/python/eval_trial_isolation -p "test_*.py"
```

## Expected output

```
shared                       passed 2/3  ['out of budget before create_refund', 'refunded', 'already refunded']  template unchanged: True
isolated                     passed 0/3  ['out of budget before create_refund', 'out of budget before create_refund', 'out of budget before create_refund']  template unchanged: True
shared + fingerprint check   passed 0/3  ['out of budget before create_refund', 'invalid: start state differs from the template', 'invalid: start state differs from the template']  template unchanged: True
```

Five unittest cases check the isolated and shared outcomes, the fingerprint check, the budget and that the
template is never written.

## Limitations

One task, one table set and a deterministic agent. A real suite also isolates files, caches and quotas, and
records waiting time so that throttled trials can be rerun rather than scored.
