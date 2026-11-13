# WebSocket to HTTP fallback policies for model requests

**Author: Sandeep Belgavi**

A runnable companion to *Falling Back From WebSocket to HTTP for Model Requests: Why Codex 0.168 Stays on HTTP for the Session* (aicassindra.com). A scripted model comparing per-request fallback, sticky session fallback (the net behaviour of Codex CLI rust-v0.168.0 after pull requests 58950 and 58989) and background probing with recovery, under a transient outage, a proxy answering 426 and a flapping link.

## Prerequisites

- Python 3.11 or newer. Standard library only.
- `.env.example` documents that nothing secret is read from the environment. No API keys, no network calls beyond loopback.

## Sample input

Three synthetic eight-request network scripts (TRANSIENT, PROXY_426, FLAPPING).

## Commands

From this directory:

```
python fallback.py
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Transient outage: per-request WWHHWWWW with 12 WebSocket attempts, sticky WWHHHHHH with 5, probing WWHHWWWW with 9 and 2 probes. 426: every policy makes 1 attempt then 8 HTTP requests. Flapping: sticky uses 3 retries, per-request 12. 6 tests pass.

## Limitations

No real transport, latency or cost; the network script does not change within a request. It does not reproduce Codex internals.

Views are my own and do not represent any employer, past or present.
