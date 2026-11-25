# Expose Only the Tools the Current Workflow State Allows

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/agents/agent_tools_scoped_by_workflow_state.html (article publication pending).

Prerequisites: CPython 3.13 (tested with 3.13.5). No third-party runtime dependencies.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

`expected.json` records the demonstration output of a successful local run. Tests cover failure boundaries and invariants; see the test file for each fixture.

Limitations: In-memory case objects; the revision check stands in for a conditional database update. No model, authorization service or real refund system. No model, SDK or provider is contacted. Views are my own and do not represent any employer, past or present.
