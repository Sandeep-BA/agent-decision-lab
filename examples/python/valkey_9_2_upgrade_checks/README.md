# Valkey 9.2 Rejects Bare Score Bounds and Saves More Often: Test Both Before Upgrading

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/databases/valkey_9_2_upgrade_behavior_changes.html (article publication pending).

Prerequisites: CPython 3.13 (tested with 3.13.5). No third-party runtime dependencies.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

`expected.json` records the demonstration output of a successful local run. Tests cover failure boundaries and invariants; see the test file for each fixture.

Limitations: Models of two merged Valkey changes (PRs 4054 and 3118), not runs against Valkey binaries. Verify against a Valkey 9.2 staging server. No model, SDK or provider is contacted. Views are my own and do not represent any employer, past or present.
