# Seeded simulation of LLM replica routing

**Author: Sandeep Belgavi**

A runnable companion to *Route LLM Requests by Outstanding Work, Not Round Robin* (aicassindra.com). Compares round robin, least outstanding requests, power-of-two-choices and least reserved KV tokens across four simulated continuous-batching replicas with mixed request lengths.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

1,200 requests from `make_requests(seed=3, rate=3.0)`: 90 % short (500-token prompt, cap 300), 10 % long (2,000-token prompt, cap 4,000).

## Commands

From this directory:

```
python routing.py
python -m unittest -v
```

## Expected output

Short-request p99 latency: round robin 41.16 s, least requests 16.81 s, power of two choices 20.35 s, least KV tokens 4.73 s. All 1,200 requests complete in each run. 5 tests pass (about 15 s).

## Limitations

A simulation with assumed constants (step time, KV capacity, up-front reservation), not a measurement of vLLM, SGLang or any engine. Real engines allocate KV incrementally, preempt and prefix-cache; the ranking can change with those.

Views are my own and do not represent any employer, past or present.
