# OpenAI-compatible endpoint conformance suite

**Author: Sandeep Belgavi**

A runnable companion to *OpenAI-Compatible Is Not Identical: A Conformance Suite for Chat Completions Across
Providers and Local Servers* (aicassindra.com, LLM). Many servers accept the Chat Completions request shape and
silently ignore parts of it. `conformance.py` sends thirteen small requests and checks what each field actually
did, reporting PASS, DIFF (answered, but not as the reference behaves) or FAIL.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install.
- Offline tests need nothing else: they start `fake_server.py` on ephemeral local ports.
- A live run needs a server you are allowed to call. For a local run, Ollama with a small model, for example
  `ollama pull qwen2.5:0.5b-instruct`. For a hosted endpoint, put your key in `OPENAI_COMPAT_API_KEY`
  (see `.env.example`); requests are billed by that provider.

## Commands

```
python -m unittest discover -s . -p "test_*.py"                                   # offline tests
python fake_server.py --profile lenient --port 8899                               # optional: a local fake
python conformance.py --base-url http://127.0.0.1:8899/v1 --model fake            # suite against the fake
python conformance.py --base-url http://127.0.0.1:11434/v1 --model qwen2.5:0.5b-instruct   # live, Ollama
python conformance.py --base-url <url> --model <model> --json > result.json      # keep as a CI artifact
```

## Sample input and recorded output

`fixtures/ollama-0.40.6-qwen2.5-0.5b-2026-10-25.json` is the JSON output of a real run on 25 October 2026 on
Windows 11 against Ollama 0.40.6 with `qwen2.5:0.5b-instruct`. It was run three times that day with the same
verdicts: nine PASS and four DIFF (`max_completion_tokens` ignored, `n` ignored, an unknown parameter accepted
with HTTP 200, and the first seeded reply differing from later identical requests).

## Expected output

The offline tests assert that the `strict` fake passes every check, that the `lenient` fake produces exactly the
four recorded DIFFs, that the recorded Ollama verdicts match the lenient profile, and that an unreachable server
never yields a PASS (that test waits for connection timeouts and takes about half a minute on Windows).

## Limitations

The checks use tiny prompts and a small model, so content-dependent checks (stop sequence, JSON modes) can vary by
model; rerun with your own model. A PASS means the observed behaviour matched for these requests, not that a
server is fully compatible. The fake server returns canned text and is only a test double. Hosted compatibility
layers were not called for the article; read their documentation and run the suite with your own key.
