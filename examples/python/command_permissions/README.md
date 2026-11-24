# A Trusted MCP Configuration Still Needs Trusted Executable Paths

Author: **Sandeep Belgavi**. Original explanation, code and synthetic fixtures.

Audit system-configured command ownership, writable ancestors and wrapper dependency closure independently of server-name allowlists.

Article destination (publication pending): https://aicassindra.com/blogs/security/gemini_system_mcp_command_permissions.html

## Prerequisites

CPython 3.13.5. No third-party dependencies; requirements.txt intentionally contains no packages.

## Run from this directory

```text
python example.py
python -m unittest test_example -v
```

Input: `sample-input.json`. Expected output: `expected-output.json`. Tests include negative outcomes, state preservation and boundary cases. All fixtures are synthetic; no provider call occurs.

## Limits

Supplied POSIX-like resource closure only. It cannot discover omitted dependencies and does not inspect Windows ACLs, real permissions or launch any server.

Views are my own and do not represent any employer, past or present.

## Primary references

- [Gemini CLI commit 4fa64e7: system MCP command permissions; reviewed 17 November 2026](https://github.com/google-gemini/gemini-cli/commit/4fa64e71b9b4e1bb65a86cc2863574f561b82340)
