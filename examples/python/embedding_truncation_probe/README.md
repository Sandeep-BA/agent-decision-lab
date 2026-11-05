# Detecting silent truncation of embedding inputs

**Author: Sandeep Belgavi**

A runnable companion to *Embedding Inputs Longer Than the Model Limit Are Cut Off Without an Error*
(aicassindra.com, LLM). It embeds a synthetic Belgavi's Book Store returns page whose last paragraph lies past
the token limit, and runs two checks: the reported token count equals the limit, and removing the last
paragraph does not change the vector.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- Offline tests need nothing else. The optional live probe needs a local [Ollama](https://github.com/ollama/ollama)
  server with an embedding model, for example `ollama pull all-minilm`. `.env.example` shows the one variable
  the live probe reads, `OLLAMA_URL`. No API key is used.

## Commands

```
python -m unittest discover -s examples/python/embedding_truncation_probe -p "test_*.py"   # offline, fake server
python examples/python/embedding_truncation_probe/probe.py                                # offline output
python examples/python/embedding_truncation_probe/probe.py --live --model all-minilm      # calls local Ollama
```

## Expected output

Offline, against the fake server that keeps the first 256 whitespace tokens: `expected_offline_output.json`.
The long chunk and the long chunk plus its last paragraph both report 256 tokens and get the same vector.

Live run recorded on 2026-11-05 with Ollama 0.40.12 and `all-minilm` on Windows (`recorded_live_2026-11-05.json`):

| Input | Characters | Tokens reported |
| --- | --- | --- |
| Policy only | 456 | 98 |
| Policy and shipping notes | 4,176 | 256 |
| Policy, notes and damaged-items paragraph | 4,272 | 256 |
| Damaged-items paragraph alone | 96 | 22 |

Adding the last paragraph did not change the vector. The question "Can I return a damaged book after two months?"
scored 0.4839 against the long chunk and 0.8465 against the last paragraph alone. With `"truncate": false` the
server returned HTTP 400, "the input length exceeds the context length".

## Limitations

The live numbers are one run of one small model on one machine; other models, servers and versions give other
numbers, and the packaged context of a model can change between releases. The fake server tokenizes on
whitespace and builds a bag-of-words vector, so its similarity values are not comparable with a real model; it
only reproduces the truncation behaviour. A batch request may report one token count for the whole batch, so
the probe sends one input per call.
