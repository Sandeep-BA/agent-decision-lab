# Stop Restored Agent Runs When Their Model Route Is Missing

Author: **Sandeep Belgavi**. Original explanation, code and synthetic fixtures.

Bind a resumed run to a nonsecret route identity and reject missing or mismatched runtime configuration before creating a request.

Article destination (publication pending): https://aicassindra.com/blogs/agents/restored_agent_gateway_route_contract.html

## Prerequisites

CPython 3.13.5. No third-party dependencies; requirements.txt intentionally contains no packages.

## Run from this directory

```text
python example.py
python -m unittest test_example -v
```

Input: `sample-input.json`. Expected output: `expected-output.json`. Tests include negative outcomes, state preservation and boundary cases. All fixtures are synthetic; no provider call occurs.

## Limits

Nonsecret route comparison only. No login, token handling, billing, network calls, DNS, provider client or real credential resolution.

Views are my own and do not represent any employer, past or present.

## Primary references

- [Claude Code v2.1.326 release notes, 16 November 2026 UTC](https://github.com/anthropics/claude-code/releases/tag/v2.1.326)
