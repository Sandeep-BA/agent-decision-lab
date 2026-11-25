# Canary a Prompt or Model Change per Conversation, Not per Request

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/llm/llm_canary_per_conversation_assignment.html (article publication pending).

Prerequisites: CPython 3.13 (tested with 3.13.5). No third-party runtime dependencies.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

`expected.json` records the demonstration output of a successful local run. Tests cover failure boundaries and invariants; see the test file for each fixture.

Limitations: Synthetic identifiers; every conversation starts together and has the same length. FNV-1a 32-bit (RFC 9923) is used for reproducibility, not as a recommendation over other well-distributed hashes. Per-request counts depend on Python's random module. No model, SDK or provider is contacted. Views are my own and do not represent any employer, past or present.
