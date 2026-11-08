# One deadline through an agent run

**Author: Sandeep Belgavi**

Companion to *One Deadline Through an Agent Run* on aicassindra.com. `budget.py` contains the `Deadline` object from the
article and a simulated five-hop run (model, order lookup, model, refund tool, model) with a slow refund tool.

## Prerequisites
Python 3.11 or newer; standard library only. `.env.example` documents that nothing is read from the environment.

## Commands
```
python examples/python/deadline_budget/budget.py
python -m unittest discover -s examples/python/deadline_budget -p "test_*.py"
```

## Expected output
```
fixed {"finished": 29400, "overrun": 9400, "ghost": 12000, "refunds": 2, "retries": 1, "skipped": 0, "delivered": false, "fallback": false}
propagate {"finished": 19400, "overrun": 0, "ghost": 6000, "refunds": 1, "retries": 0, "skipped": 1, "delivered": true, "fallback": false}
```

## Limits
Times are simulated integers. Real calls vary in latency, streaming and cancellation behaviour, and a model call may be cut short by the provider.
