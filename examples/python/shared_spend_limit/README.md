# A spend limit shared by concurrent agent runs

**Author: Sandeep Belgavi**

A runnable companion to *A Spend Limit Shared by Concurrent Agent Runs* (aicassindra.com, LLM). Twelve agent
runs for Belgavi's Book Store share one token budget. The example compares the common check-then-spend guard
with a reserve-and-settle ledger that holds input tokens plus `max_tokens` before each call and settles the
reported usage afterwards; a failed call keeps its full hold.

**No model provider is called.** Runs are threads and the client is a fake that returns seeded usage and cuts
output at `max_tokens`, as a provider would.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/shared_spend_limit/budget.py
python -m unittest discover -s examples/python/shared_spend_limit -p "test_*.py"
```

## Expected output

Thread scheduling varies, so fleet totals differ between runs; one run printed:

```
check_then_spend {'spent': 155230, 'limit': 150000, 'over': 5230, 'completed': 7, 'stopped': 1, 'refused': 4, 'cut_at_max_tokens': 4}
reserve_per_step {'spent': 141824, 'limit': 150000, 'over': 0, 'completed': 7, 'stopped': 1, 'refused': 4, 'cut_at_max_tokens': 4}
gap_demo         {'limit': 10000, 'spent': 33954, 'calls': 8}
```

`gap_demo` is deterministic: eight calls pass the check before any usage is recorded and spend 33,954 tokens
against a 10,000-token limit. Six unittest cases check that, that reservations never exceed the limit across
five seeds with 16 concurrent runs, that a large budget completes every run, that a failed call keeps its hold,
that a refused reservation spends nothing, and that output is cut at `max_tokens`.

## Limitations

The ledger is in memory with a lock. In production it is a conditional update in a shared store, settlement may
arrive minutes later from a usage pipeline, holds need an expiry, and cached or reasoning tokens need their own
weighting. The interactive lab on aicassindra.com explores per-run reservations and reporting delay.
