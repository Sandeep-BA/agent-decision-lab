# Layered HTTP client timeouts in undici

**Author: Sandeep Belgavi**

A runnable companion to *Silent Streams and the Five-Minute bodyTimeout: Layered HTTP Client Timeouts in Node.js undici* (aicassindra.com). A loopback server streams one chunk, goes silent, then finishes. The probe measures undici's headersTimeout, bodyTimeout and an overall AbortSignal.timeout deadline at scaled-down times.

## Prerequisites

- Node.js 20.18.1 or newer (tested with 22.17.0). npm install fetches the pinned undici 7.30.2.
- `.env.example` documents that nothing secret is read from the environment. No API keys, no network calls beyond loopback.

## Sample input

Synthetic SSE chunks about CASE-9120 and the timings in CASES (probe.mjs).

## Commands

From this directory:

```
npm install
node probe.mjs
node --test
```

## Expected output

Recorded with undici 7.30.2: a 300 ms silence under a 1 s bodyTimeout completes; a 1.5 s silence fails with UND_ERR_BODY_TIMEOUT even when headersTimeout and the deadline are 3 s; raising bodyTimeout to the deadline completes; a slow first byte fails with UND_ERR_HEADERS_TIMEOUT; a deadline shorter than both ends with TimeoutError. Timers fired up to about 0.5 s late, as the undici documentation warns. 2 tests pass (about 10 s).

## Limitations

Loopback only, scaled times, one HTTP/1.1 connection. Node.js's built-in fetch bundles its own undici version.

Views are my own and do not represent any employer, past or present.
