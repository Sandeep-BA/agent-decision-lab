# Passing reasoning state back across tool calls through a provider-neutral transcript store

**Author: Sandeep Belgavi**

A runnable companion to *Passing Reasoning State Back Across Tool Calls* (aicassindra.com, LLM). Many agent
frameworks persist conversations in a provider-neutral shape: text plus tool calls. That shape has no place for
Anthropic `thinking` / `redacted_thinking` blocks, OpenAI Responses `reasoning` items with `encrypted_content`,
or Gemini `thoughtSignature` fields, so they disappear between the tool call and the tool result. This example
stores the provider payload opaquely next to the neutral form and replays it verbatim when the next request
goes to the same provider and model family.

**No provider is called.** The three responses in `transcript.py` are synthetic fixtures shaped after the
documented formats; `check()` applies the documented round-trip rules locally. It is not the providers' own
validation, and a real request can fail for reasons this check does not model.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/reasoning_state_passthrough/transcript.py
python -m unittest discover -s examples/python/reasoning_state_passthrough -p "test_*.py"
```

## Expected output

| Store | anthropic | openai | gemini |
| --- | --- | --- | --- |
| neutral only (`keep_native=False`) | thinking blocks missing | reasoning item missing | signature part missing |
| neutral plus native payload | no violations | no violations | no violations |

The tests also show two common bugs: keeping only blocks of type `thinking` (which silently drops
`redacted_thinking`) and merging Gemini parts (which moves the signature off its original part), and that a
switch to another model family falls back to the neutral form.

## Limitations

One assistant turn per fixture, no streaming, and no cross-family compatibility tables: providers decide which
earlier reasoning a different model can read and drop the rest themselves. Store the native payload as opaque
data, and never edit or summarise it.
