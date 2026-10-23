# Pacing an agent fleet from rate-limit headers

**Author: Sandeep Belgavi**

A runnable companion to *Pacing an Agent Fleet From Provider Rate-Limit Headers: Request and Token Limits,
Reset Times, 429s and Shared Budgets* (aicassindra.com, LLM). Instead of hammering into 429s and retrying,
read the remaining-token headers the provider returns on every response and slow down before you are
refused. The pacer uses token headroom, the binding limit, and waits until the reported reset time. A
separate classifier tells a retryable refusal from a spend cap that must never be retried.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install.
- No network and no provider call. Header dicts and error bodies are synthetic, and the clock is passed in.
  `.env.example` documents that nothing is read from the environment.

## Sample input

Synthetic header sequences and error bodies are built in `pacer.demo()` and in the tests;
`fixtures/headers.json` records the default 2,000,000 tokens-per-minute limit. The modelled headers are the
Anthropic `anthropic-ratelimit-tokens-*` set; OpenAI `x-ratelimit-*` and Gemini have the same shape.

## Commands

```
python pacer.py                                        # show a wait decision and a spend-cap classification
python -m unittest discover -s . -p "test_*.py"        # run the tests
```

## Expected output

`pacer.py` prints a non-zero wait when only 80,000 of 2,000,000 tokens remain (4 percent, below the 5
percent floor) and classifies a spend-cap 429 as `stop`. The tests assert the pacer proceeds at 25 percent
headroom and waits at 4 percent, that it paces before remaining tokens reach zero, that a spend-cap 429 is
never retried while an ordinary 429 honours Retry-After and a 529 backs off, and that cached input tokens
are excluded from the effective ITPM count.

## Limitations

The model treats headers as exact and the reset as an absolute time; real headers are rounded to the
nearest thousand and the Anthropic limit replenishes continuously under a token bucket. A real fleet must
share the remaining counts across clients and add jitter to backoff. The numbers here are illustrative, not
a benchmark, and no request is ever sent.
