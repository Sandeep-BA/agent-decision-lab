# Assembling streamed tool-call arguments across providers

**Author: Sandeep Belgavi**

A runnable companion to *Assembling Streamed Tool-Call Arguments Across Providers* (aicassindra.com, LLM). A
provider-neutral accumulator keyed by block or item index, adapters for the Claude Messages, OpenAI Responses
and Gemini Interactions streaming event shapes, and an execution gate for a book-shop `issue_refund` tool.

**No API is called.** The streams are synthetic recordings shaped like each provider's documented events,
built in code so that tests can re-split them at every position.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/streamed_tool_call_assembler/assembler.py
python -m unittest discover -s examples/python/streamed_tool_call_assembler -p "test_*.py"
```

## Expected output

```
claude             toolu_A  execute
claude             toolu_B  execute
openai             call_1   execute
gemini             fn_1     execute
claude truncated   toolu_A  error
claude truncated   toolu_B  execute
```

The truncated stream ends after the amount, as a response stopped by `max_tokens` would; the gate returns an
error tool result with the raw input under `INVALID_JSON` and never executes the refund. Eight unittest cases
cover every two-piece split, a split inside a `\u2014` escape, interleaved parallel calls, the OpenAI done
event overriding a lossy concatenation, Gemini assembly on completion and the amount check.

## Limitations

The recordings follow the documented event names and fields but are not captured from live APIs, and the
adapters ignore event types that do not concern tool calls. Validate against your provider SDK version.
