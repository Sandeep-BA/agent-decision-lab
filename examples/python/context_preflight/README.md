# Context preflight: count before sending, then shrink in a fixed order

**Author: Sandeep Belgavi**

A runnable companion to *When the Next Agent Request Will Not Fit* (aicassindra.com, LLM). Before each model
call, the returns assistant at Belgavi's Book Store checks that the request fits:
budget = context window - max output tokens - a safety margin (5% of the window by default). If it does not
fit, `fit()` shrinks it in a fixed order: clear tool results older than the last two user turns, oldest first,
to a short stub; then remove the oldest whole turns. It never touches the system prompt, the tool definitions or
the latest turns. If the request still does not fit, it raises `ContextBudgetError` instead of sending.
`classify_provider_error` maps a provider's 400, 413 or 429 to an action.

**No model is called.** Counting is injected. The demo uses `approx_count`, a rough 4-characters-per-token
estimate of the JSON body that is **not** any provider's tokenizer. In production pass the provider's token
counting call. The message format (`role: tool`) is a simplified generic shape, not any one provider's schema.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` lists nothing to install.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/context_preflight/preflight.py
python -m unittest discover -s examples/python/context_preflight -p "test_*.py"
```

## Expected output

```
approx tokens before: 9438
budget 6100 before 9438 after 5007
 - cleared tool result lookup-1 (6000 chars)
 - cleared tool result lookup-2 (6000 chars)
 - cleared tool result lookup-3 (6000 chars)
refused: request needs 3179 tokens, budget is 1350 after removing everything removable
context overflow: re-run fit() with a smaller budget, do not retry unchanged
```

Six unittest cases: the demo plan, the protected parts (system prompt, tools, last two turns and their tool
results) when whole turns must go, refusal, an unchanged request that already fits, an injected counter with a
large overhead, and the budget arithmetic and error mapping.

## Limitations

The error patterns are narrow examples; build yours from the error bodies your providers actually return. A
cleared tool result may be needed again: the stub tells the model to call the tool again, which costs a call.
Counting endpoints return estimates and have their own rate limits, so keep a margin.
