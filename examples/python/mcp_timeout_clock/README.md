# Time Out MCP Requests With a Clock That Progress Can Reset and a Ceiling It Cannot

Author: **Sandeep Belgavi**.

Original teaching example for https://aicassindra.com/blogs/mcp/mcp_request_timeout_progress_ceiling.html.

`example.py` models a client request clock: an idle timeout, an optional reset on each progress notification and a maximum total. Two ceiling modes are compared: `sdk`, where the ceiling is checked only when a progress notification arrives (how `Protocol._resetTimeout` in the TypeScript SDK main branch reads on 2026-11-27), and `timer`, where the ceiling is its own timer, as with an `AbortSignal.timeout` passed as the request signal.

Prerequisites: CPython 3.11 or newer (recorded with 3.13.5 on Windows 11). Standard library only; `requirements.txt` is intentionally empty and `.env.example` documents that nothing is read from the environment. No network, no credentials and no model call.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json` (a request that stops sending progress at 290 s waits until 350 s in `sdk` mode and is cancelled at 300 s in `timer` mode).

Limitations: a model of timing and cancellation only; it does not speak MCP. SDK behaviour can change between releases, so re-read the source of the version you pin. Views are my own and do not represent any employer, past or present.
