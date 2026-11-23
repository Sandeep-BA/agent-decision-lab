# MCP prompt arguments: name-matched versus explicit

**Author: Sandeep Belgavi**

A runnable companion to *ADK Python 2.15.0 Stops MCP Prompts From Choosing Which Session State They Receive* (aicassindra.com). Models how McpInstructionProvider chose prompt arguments before ADK Python 2.15.0 (every server-declared name filled from session state) and after (only the caller's `arguments=` mapping or callable, nothing by default), plus an allowlist binder for migration that refuses sensitive keys and reports what a server asks for but will not receive.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Synthetic session state with locale, case id, a first name, an email, a placeholder OAuth credential and a cached tool result; two servers, one of which declares the sensitive names as prompt arguments.

## Commands

From this directory:

```
python binding.py
python -m unittest -v
```

## Expected output

Name-matched against the hostile server sends the email, credential and tool result. The 2.15.0 default sends nothing (`arguments=None`). The allowlist sends locale and case id to both servers and reports three declared-not-sent names for the hostile one. 7 tests pass.

## Limitations

Does not import ADK or start an MCP server; it models the argument choice only. Install `google-adk>=2.15.0` and read its `McpInstructionProvider` to see the real signature.

Views are my own and do not represent any employer, past or present.
