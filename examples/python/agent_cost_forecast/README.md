# Forecasting an agent feature's token cost from a pilot, and checking it against week one

**Author: Sandeep Belgavi**

A runnable companion to *Forecasting What an Agent Feature Will Cost Before Launch* (aicassindra.com, LLM).
It models one agent run whose context grows every step, prices it with and without prompt caching in
input-token equivalents, bootstraps a weekly forecast from 60 pilot runs, and compares it with a synthetic
first week whose share of long runs is higher than the pilot's.

**No model is called.** Pilot and week-one runs are synthetic step counts generated from fixed seeds, and the
token sizes per step are constants at the top of `forecast.py`. The cache multipliers (read 0.1, write 1.25)
and the output weight (5.0) are illustrative; take yours from your provider's price sheet. Nothing is
converted to money.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/agent_cost_forecast/forecast.py
python -m unittest discover -s examples/python/agent_cost_forecast -p "test_*.py"
```

## Expected output (abridged)

| Quantity | Value |
| --- | --- |
| 8-step run: input, output, cache read, cache write | 96,400 / 2,400 / 85,100 / 11,300 tokens |
| 16-step run: input | 288,800 tokens (3.0 times the 8-step run) |
| 8-step run in input-token equivalents, cached / uncached | 34,635 / 108,400 |
| Pilot: runs, mean steps, runs of 18+ steps, top 10% share of cost | 60, 7.48, 2, 21.5% |
| Bootstrap forecast for 1,400 cases (p10 / p50 / p90) | 45,142,195 / 46,008,660 / 46,876,350 |
| Week one: mean steps, runs of 18+ steps, actual | 9.79, 234, 65,996,465 |
| Pilot re-weighted with week one's long-run share | 62,165,977 |

The bootstrap interval is narrow because it only measures resampling noise in the pilot. Week one lands far
above it because long runs are 16.7% of cases instead of 3.3%; re-weighting the pilot by that share explains
most of the gap.

## Limitations

Every step adds the same number of output and tool-result tokens, the cache is always warm, and there are no
retries, failures or reasoning tokens. Real runs vary per step, caches expire between sparse requests, and
pricing has more meters than two multipliers. Use the structure, not the constants.
