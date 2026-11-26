# Treat MCP Tool Annotations as Server Claims, Not as Your Approval Policy

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/mcp/mcp_tool_annotations_untrusted_hints.html.

Two synthetic MCP servers for the fictional Belgavi's Book Store, one trusted and one untrusted, list tools with and without annotations. A naive policy that believes `readOnlyHint` auto-runs a mislabelled `delete_note`. A host policy applies the schema defaults, uses a host-owned classification pinned to a digest of each tool definition, lets hints only tighten a decision, and asks whenever an untrusted tool is unclassified or its definition changed.

Prerequisites: CPython 3.11 or newer (tested with 3.13.5). No third-party dependencies (`requirements.txt` is intentionally empty). `.env.example` documents that nothing is read from the environment.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json` (asserted by the tests).

Limitations: no MCP client, server or transport is used; tool listings are literal dictionaries shaped like `tools/list` results. The policy is a teaching sketch, not a complete authorization system. Views are my own and do not represent any employer, past or present.
