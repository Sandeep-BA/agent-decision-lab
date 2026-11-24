# Reject Incomplete Agent Plan Graphs Before Any Tool Runs

Author: **Sandeep Belgavi**. Original explanation, code and synthetic fixtures.

Compile a proposed graph against a closed operation registry; reject dangling dependencies and disconnected cycles before any effect.

Article destination (publication pending): https://aicassindra.com/blogs/system_design/agent_plan_graph_closed_registry.html

## Prerequisites

CPython 3.13.5. No third-party dependencies; requirements.txt intentionally contains no packages.

## Run from this directory

```text
python example.py
python -m unittest test_example -v
```

Input: `sample-input.json`. Expected output: `expected-output.json`. Tests include negative outcomes, state preservation and boundary cases. All fixtures are synthetic; no provider call occurs.

## Limits

Validates a fixed graph only. No real model, tools, authorization, persistent scheduler or remote effects.

Views are my own and do not represent any employer, past or present.

## Primary references

- [Python 3.13 graphlib: predecessor registration and cycle detection](https://docs.python.org/3.13/library/graphlib.html)
