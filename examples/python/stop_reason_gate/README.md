# Check the stop reason before parsing model output

**Author: Sandeep Belgavi**

A runnable companion to *Truncated Model Output: Check the Stop Reason Before You Parse* (aicassindra.com). Maps the stop or finish reason of OpenAI Chat Completions, the OpenAI Responses API, the Anthropic Messages API and the Gemini API to one category, and parses structured output only when generation completed. It also shows why repairing truncated JSON is unsafe.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

Hand-written response bodies in `FIXTURES`, written from the providers' documented fields. They are not recorded provider responses.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Eight tests pass. All four truncated fixtures are refused with a retry action; unknown reasons are never treated as complete; the naive repair keeps 2 of 5 case ids and still parses.

## Limitations

Field names follow provider documentation read on 2026-11-11 and can change. No provider was called. Streaming responses, where the reason arrives in the final event, are not covered.

Views are my own and do not represent any employer, past or present.
