# Prompt-cache prefix audit for agent loops

**Author: Sandeep Belgavi**

A runnable companion to *Keeping the Prompt Cache Warm in Agent Loops: Prefix Breakers, Breakpoints, TTL
Gaps and Reading the Usage Fields* (aicassindra.com, llm). It has two parts:

- `first_divergence(prev, cur)` reports the first block at which two consecutive requests differ, the
  quickest way to find what breaks a cached prefix;
- `simulate(requests)` replays a request sequence against a simplified model of documented prefix
  caching: entries are written only at breakpoints, a read looks back at most 20 blocks from each
  breakpoint for an entry an earlier request wrote, entries expire after a TTL that each read refreshes,
  and prefixes under a minimum length (1,024 tokens by default) are not cached. Costs use 1.25 for a
  5-minute write and 0.1 for a read, relative to an uncached input token.

Blocks carry explicit token counts, so no tokenizer is needed. This is a teaching model built from the
providers' documentation, not a reimplementation of any provider. In production, read the real usage
fields: `cache_creation_input_tokens` and `cache_read_input_tokens` on the Claude API,
`input_tokens_details.cached_tokens` on the OpenAI Responses API.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt`).
- No environment variables or credentials (`.env.example`). Nothing calls a model provider.

## Commands

From the repository root:

```sh
python examples/python/prompt_cache_audit/cache_audit.py
python examples/python/prompt_cache_audit/cache_audit.py --variant tool_order --rows
python examples/python/prompt_cache_audit/cache_audit.py --variant approval_pause --ttl 3600
python -m unittest discover -s examples/python/prompt_cache_audit -p "test_*.py"
```

## Expected output (verified with Python 3.13)

A ten-request refunds-agent loop: four tool definitions (1,400 tokens), a 1,800-token system prompt, and
550 tokens of history added per turn; a breakpoint after the system prompt and one on the last block.

| Variant | What changes | Hit rate | Input cost vs no caching |
| --- | --- | --- | --- |
| `stable` | nothing | 85.9% | 26.2% |
| `timestamp` | the system prompt carries the request time | 0.0% | 125.0% |
| `tool_order` | tool order rotates from request 5 | 77.3% | 36.1% |
| `compaction` | turns 1 to 5 replaced by a summary from request 6 | 82.0% | 30.7% |
| `approval_pause` | a six-minute pause before request 6 | 76.4% | 37.2% |
| `approval_pause --ttl 3600` | same pause with a one-hour TTL | 85.9% | 26.2% |

The one-hour row ignores the higher write price of a one-hour entry (2x on the Claude API); price it
before choosing it.

## Tests

`test_cache_audit.py` (8 tests): appending is not a divergence; reordered tools diverge at block 0; the
stable, timestamp, tool-order and pause figures above; the 20-block lookback misses an entry 25 blocks
back unless a second breakpoint sits on it; a prefix under the minimum is not cached.

## Limits

Real providers differ in detail: automatic breakpoints, per-model minimum lengths, TTL options, routing
between machines and rounding of reported counts. Treat the simulation as a way to find prefix breakers
before you measure, not as a price calculator.
