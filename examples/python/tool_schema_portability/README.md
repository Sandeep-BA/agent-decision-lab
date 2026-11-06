# One tool schema, four consumers: a portability check

**Author: Sandeep Belgavi**

A runnable companion to *One Tool Schema, Four Consumers: What Survives MCP, Gemini, OpenAI and Claude*
(aicassindra.com, LLM). `portability.py` checks a tool's JSON Schema against keyword subsets taken from the
OpenAI Structured Outputs documentation, the Claude structured-outputs limitations (shared by strict tool use)
and the google-genai 3.0.0 SDK's typed `JSONSchema` class, and builds a portable core per target by dropping
refused keywords and moving numeric and length limits into the description. The fixture is the fictional
Belgavi's Book Store `resolve_case` tool.

## Prerequisites

- Python 3.11 or newer. The check itself uses only the standard library.
- Optional: `pip install -r requirements.txt` (google-genai 3.0.0, pinned) to run the SDK conversion tests. They
  are offline: no API key, no network call. Without the package they are skipped.

## Commands

```
python examples/python/tool_schema_portability/portability.py examples/python/tool_schema_portability/fixtures/resolve_case.json
python -m unittest discover -s examples/python/tool_schema_portability -p "test_*.py"
```

## Expected output

```
openai_strict ["$: every property must be required (missing note)"]
claude_strict ["$.properties.case_id: maxLength", "$.properties.case_id: minLength", "$.properties.amount: maximum", "$.properties.amount: minimum", "$.properties.amount: multipleOf"]
gemini_sdk_schema ["$.properties.amount: multipleOf"]
claude core {"type": "number", "description": "(minimum 0, maximum 500, multipleOf 0.01)"}
```

With google-genai 3.0.0 installed, three more tests pin what the SDK did on 2026-11-06: `Schema.from_json_schema`
dropped `additionalProperties: false`, turned `anyOf` of string and null into `nullable`, and kept `pattern`; the
typed `JSONSchema` class rejected `multipleOf`; `parameters_json_schema` passed the dictionary through unchanged.

## Limitations

The subsets are documentation encoded as data, not the providers' grammars, and the OpenAI page is ambiguous
about `minLength` and `maxLength` in strict mode. Nothing here calls a provider. Send one real request per
provider with the generated schema before production, and always validate tool arguments on the server with the
full schema.
