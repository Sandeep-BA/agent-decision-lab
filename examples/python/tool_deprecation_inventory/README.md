# Retire a Tool That Agents Still Call: Deprecation and Sunset Signals, Caller Inventory and Aliases

Author: **Sandeep Belgavi**.

Original teaching example for https://aicassindra.com/blogs/agents/agent_tool_deprecation_sunset.html.

`example.py` formats the `Deprecation` (RFC 9745) and `Sunset` (RFC 8594) fields with a `Link` of relation `deprecation`, rejects a sunset earlier than the deprecation, writes a tool listing that carries the notice in its description and a namespaced `_meta` key (MCP tool definitions have no deprecation field), translates old calls through a deterministic alias that refuses unknown argument shapes, groups a synthetic gateway log by caller and prompt version, and only allows removal when the sunset has passed and the inventory is empty.

Prerequisites: CPython 3.11 or newer (recorded with 3.13.5 on Windows 11). Standard library only; `requirements.txt` is intentionally empty and `.env.example` documents that nothing is read from the environment. No network, no credentials and no model call.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json`.

Limitations: the plan dates and log are synthetic; the alias handles one argument rename. Clients are free to ignore both fields, which is why the inventory, not the header, gates removal. Views are my own and do not represent any employer, past or present.
