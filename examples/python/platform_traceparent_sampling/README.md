# An unsampled platform traceparent and parent-based sampling

**Author: Sandeep Belgavi**

A runnable companion to *An Unsampled Platform traceparent Can Drop Every Agent Span: Parent-Based Sampling at a Trust Boundary* (aicassindra.com). A measurement with the real OpenTelemetry Python SDK and an in-memory exporter: a server span, a model span and a tool span under ParentBased(root=ALWAYS_ON), with four ways to treat an inbound traceparent (continue, ignore, link, dedicated caller header).

## Prerequisites

- Python 3.11 or newer.
- `.env.example` documents that nothing secret is read from the environment. No API keys, no network calls beyond loopback.

## Sample input

Synthetic W3C traceparent values with the sampled flag 00 and 01, and a caller header.

## Commands

From this directory:

```
python -m pip install -r requirements.txt
python sampling_probe.py
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Recorded with opentelemetry-sdk 1.45.2: continuing the unsampled platform parent exports 0 of 3 spans; ignore, link and dedicated export 3 (link adds 1 span link); a sampled platform parent exports 3 under every mode; the dedicated mode keeps the caller trace id 4bf92f3577b34da6a3ce929d0e0e4736. 5 tests pass.

## Limitations

No web framework, collector or platform is involved; FastAPI was not run. The exporter is in memory.

Views are my own and do not represent any employer, past or present.
