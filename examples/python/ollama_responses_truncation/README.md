# Context overflow and truncation on an OpenAI-compatible Responses endpoint

**Author: Sandeep Belgavi**

A runnable companion to *Ollama 0.40.16: The Responses API Stops Truncating Long Inputs Silently* (aicassindra.com). Builds Responses requests with an explicit `truncation` value, recognises context-overflow errors with anchored patterns, and keeps a recorded result from one local Ollama 0.40.16 run for the offline tests. `--live` repeats the request against your own server.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- Offline tests need no network. `--live` needs a running Ollama (or another compatible server) set in `OLLAMA_URL` and a pulled model in `OLLAMA_MODEL`; see `.env.example`. No credentials.

## Sample input

The live mode builds a synthetic 900-line help-desk log (58,203 characters) followed by a question.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
python truncation.py --live
```

## Expected output

Five offline tests pass. In the recorded run (Ollama 0.40.16, qwen2.5:1.5b, 4096-token context) `truncation` omitted or `disabled` returned HTTP 400 for a 27,599-token request; `auto` returned 200 with status `completed` and 2,050 input tokens; the native `/api/chat` without `truncate` also kept 2,050 tokens.

## Limitations

One run, one model, one machine. Token counts depend on the model tokenizer and the server context setting. The recorded fixture is evidence of that run only.

Views are my own and do not represent any employer, past or present.
