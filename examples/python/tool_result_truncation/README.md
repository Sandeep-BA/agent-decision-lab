# Cap Large Tool Results With a Truncation Record the Agent Can See

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/agents/agent_tool_result_truncation_record.html (article publication pending).

Prerequisites: CPython 3.13 (tested with 3.13.5). No third-party runtime dependencies.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

`expected.json` records the demonstration output of a successful local run. Tests cover failure boundaries and invariants; see the test file for each fixture.

Limitations: Byte budgets over compact JSON; token budgets need a tokenizer. Offset paging assumes the underlying data does not change between pages. No model, SDK or provider is contacted. Views are my own and do not represent any employer, past or present.
