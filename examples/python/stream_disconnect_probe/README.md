# Does a disconnect stop generation?

**Author: Sandeep Belgavi**

Companion to *When the Client Disconnects, Does the GPU Stop?* The probe times a queued request B behind a request A that either completes or whose client hangs up early.

## Prerequisites
Python 3.11 or newer; standard library only. The optional real run needs Ollama with `OLLAMA_NUM_PARALLEL=1` and a small model pulled.

## Commands
```
python -m unittest discover -s examples/python/stream_disconnect_probe -p "test_*.py"
python examples/python/stream_disconnect_probe/probe.py
```

## Expected shape (optional real run)
```
control median B first-chunk wait 1.95 s
disconnect median B first-chunk wait 0.055 s
```
Those figures are from the article's run of an equivalent script on one small model, not from this exact file; expect the same shape, not the same numbers. The unit tests use a stub server, so they make no model call.

## Limits
Cancellation depends on the server and every proxy between client and server, so test through each layer you run.
