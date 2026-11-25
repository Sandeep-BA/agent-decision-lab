# Mutation-Test the Deterministic Guards Around an Agent

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/agents/agent_guard_mutation_testing.html (article publication pending).

Prerequisites: CPython 3.13 (tested with 3.13.5). No third-party runtime dependencies.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

`expected.json` records the demonstration output of a successful local run. Tests cover failure boundaries and invariants; see the test file for each fixture.

Limitations: A teaching mutation harness with five operator families. It does not detect equivalent mutants automatically, and crash kills are not separated from assertion kills. Use mutmut or PIT for real codebases. No model, SDK or provider is contacted. Views are my own and do not represent any employer, past or present.
