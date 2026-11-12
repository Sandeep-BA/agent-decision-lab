# Shared MCP connection with per-chat leases

**Author: Sandeep Belgavi**

A runnable companion to *One MCP Server Process, Many Agent Chats: Shared Connections and Per-Chat Leases* (aicassindra.com). An in-process model of one stdio-style MCP connection shared by two chats: connection-scoped state bleed, host-assigned lease ids in `_meta`, overriding caller-supplied lease values, connection-wide request ids and cancel-before-release.

## Prerequisites

- Python 3.11 or newer. Standard library only. No MCP server process, no network, no model.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Geetha's chat works CASE-4410, Jenya's chat works CASE-4415. `python leases.py` prints the notes each scenario writes.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Six tests pass. Without leases the first note lands on CASE-4415. With leases each chat writes to its own case. A spoofed lease is overridden. Releasing without cancelling writes "refund approved" after the chat closed.

## Limitations

The lease key `com.example.store/lease` and the release method are invented for the example; the Codex CLI extension has its own names. The model does not implement JSON-RPC framing, initialisation or capability negotiation.

Views are my own and do not represent any employer, past or present.
