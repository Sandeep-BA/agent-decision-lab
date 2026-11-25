# Redis 8.12 Expires Set Members Individually: SEXPIRE Rules That Surprise

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/databases/redis_8_12_set_member_expiration.html (article publication pending).

Prerequisites: CPython 3.13 (tested with 3.13.5). No third-party runtime dependencies.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

`expected.json` records the demonstration output of a successful local run. Tests cover failure boundaries and invariants; see the test file for each fixture.

Limitations: A model of the redis.io command pages read on 2026-11-25. It reproduces every documented example but was not run against a Redis 8.12 server. Seconds-resolution commands only. No model, SDK or provider is contacted. Views are my own and do not represent any employer, past or present.
