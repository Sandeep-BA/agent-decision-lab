# Client-side acceptance of MCP structuredContent

**Author: Sandeep Belgavi**

A runnable companion to *Validating MCP structuredContent Against outputSchema on the Client* (aicassindra.com). A fail-closed policy for tools/call results that declare an outputSchema: tool errors, missing structured content, schema violations and unsupported schemas each get a distinct status.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

`ORDER_STATUS_TOOL` in `check_result.py` plus valid and invalid results in the tests.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Seven tests pass, including rejection of a string "false" for a boolean, an extra field, a remote `$ref` that is never fetched and an unsupported `oneOf`.

## Limitations

The validator supports a small JSON Schema subset on purpose and rejects everything else. Production clients should use a maintained JSON Schema 2020-12 validator and keep the same policy decisions around it. No MCP server or network is used.

Views are my own and do not represent any employer, past or present.
