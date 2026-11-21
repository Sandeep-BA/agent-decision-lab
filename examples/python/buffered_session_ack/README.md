# When is a buffered ADK turn durable?

**Author: Sandeep Belgavi**

A runnable companion to *Flush Buffered ADK Sessions Before Reporting a Durable Turn* (aicassindra.com). Uses the real, experimental `BufferedSessionService` from google-adk 2.15.0 over an `InMemorySessionService` subclass that waits 50 ms per stored event and can fail one write. Appends the four events of one synthetic help-desk turn and records what the wrapped store holds when each acknowledgement policy would answer the client.

## Prerequisites

- Python 3.10 or newer (run here with CPython 3.13.5). `pip install -r requirements.txt` in a virtual environment. No model is called, so no API key is needed.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Four events for CASE-9101 in `TEXTS`.

## Commands

From this directory:

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   (Windows; .venv/bin/python on Linux/macOS)
python buffered_ack.py
python -m unittest -v
```

## Expected output

Ack after append: the session object has 4 events, the store 0. Flush then ack: the store has 4. Third write fails: `flush_session` raises `SessionPersistenceError` caused by the `ConnectionError`, the store keeps 2 events, and a later `aclose()` does not report it again; acking after append learns of it only at `aclose()`. 5 tests pass. ADK logs an EXPERIMENTAL warning.

## Limitations

In-memory store with an artificial delay; no Runner, model, database or crash. Timings vary by machine.

Views are my own and do not represent any employer, past or present.
