# Make Tool Argument Defaults Explicit Before Validation and Approval

Author: **Sandeep Belgavi**. Original explanation, code and synthetic fixtures.

Separate schema annotations, versioned argument normalization and the exact effective payload sent to an adapter.

Article destination (publication pending): https://aicassindra.com/blogs/agents/tool_schema_defaults_explicit_normalization.html

## Prerequisites

CPython 3.13.5. No third-party dependencies; requirements.txt intentionally contains no packages.

## Run from this directory

```text
python example.py
python -m unittest test_example -v
```

Input: `sample-input.json`. Expected output: `expected-output.json`. Tests include negative outcomes, state preservation and boundary cases. All fixtures are synthetic; no provider call occurs.

## Limits

A narrow handwritten contract, not a complete JSON Schema validator or provider test.

Views are my own and do not represent any employer, past or present.

## Primary references

- [JSON Schema annotations: default does not insert values](https://json-schema.org/understanding-json-schema/reference/annotations)
