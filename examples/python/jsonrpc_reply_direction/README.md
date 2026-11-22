# JSON-RPC ids belong to their sender

**Author: Sandeep Belgavi**

A runnable companion to *MCP Request IDs Belong to Their Sender, So a Reply Cannot Answer Yours* (aicassindra.com). A client has its own request id 7 pending when the server sends a request that also uses id 7. The client POSTs its reply. A naive client dispatches any JSON-RPC response in the HTTP body of that reply POST by id; a strict client requires 202 or 204 for a reply POST and treats anything else as an error, the rule openai/codex PR 63075 added (merged 2026-11-22).

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Synthetic messages in `scenario()`.

## Commands

From this directory:

```
python correlate.py
python -m unittest -v
```

## Expected output

Naive client with HTTP 409 or 200: its own request 7 is resolved with the server's rejection of the reply, and the real result is then dropped. Strict client: the reply POST errors and request 7 receives its real result. 202 and 204 are acknowledged in both. 6 tests pass.

## Limitations

A model of correlation logic, not an MCP SDK or server. MCP revision 2026-07-28 no longer lets clients POST responses at all on Streamable HTTP; the collision applies to revisions 2025-03-26 through 2025-11-25, which still allow server requests and client reply POSTs.

Views are my own and do not represent any employer, past or present.
