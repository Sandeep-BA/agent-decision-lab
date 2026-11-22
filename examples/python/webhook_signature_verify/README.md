# Verify webhook signatures on raw bytes

**Author: Sandeep Belgavi**

A runnable companion to *Verify Webhook Signatures on Raw Bytes With a Replay Window* (aicassindra.com). A receiver in the Standard Webhooks symmetric style: HMAC-SHA256 over msg_id.timestamp.body, base64, v1 prefix. It checks headers, a 300-second timestamp tolerance, every offered signature against every current secret with hmac.compare_digest, then a replay cache keyed by webhook-id kept for twice the tolerance.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Synthetic secrets and one order.refunded event for CASE-4301 built in `run()`.

## Commands

From this directory:

```
python verify.py
python -m unittest -v
```

## Expected output

Raw body accepted; the same id again is a duplicate; the parsed and re-serialized body (87 bytes became 98) fails verification; the old secret is still accepted during rotation; a tampered body fails; a capture replayed 301 seconds later is outside the tolerance; an id containing a dot is malformed. 6 tests pass.

## Limitations

Symmetric signatures only and an in-memory replay cache. Use a shared store with expiry when several receivers run, and keep the producer's own library if it publishes one.

Views are my own and do not represent any employer, past or present.
