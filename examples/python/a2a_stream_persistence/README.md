# ADK Python 2.15.1 Withdraws the Aggregated Final Event for Streamed A2A Answers

Author: **Sandeep Belgavi**.

Original synthetic teaching model for https://aicassindra.com/blogs/adk/adk_2_15_1_a2a_streamed_answer_persistence.html.

A remote agent for the fictional Belgavi's Book Store streams an answer as A2A artifact updates (`append`, `last_chunk`) in three shapes: deltas closed only by a COMPLETED status, deltas whose final delta sets `last_chunk`, and deltas followed by the whole artifact with `append=false, last_chunk=true`. Three client behaviours are compared: per-update events with `partial = not last_chunk` (as in ADK Python v2.15.1), partials plus an aggregated final event (the idea of the 2.15.0 change that 2.15.1 reverted), and the same aggregate marked as replacing the partials. Persistence keeps only non-partial events; two displays show what an integration that appends every event, or one keyed by artifact id, would render.

Prerequisites: CPython 3.11 or newer (tested with 3.13.5). No third-party dependencies (`requirements.txt` is intentionally empty). `.env.example` documents that nothing is read from the environment.

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json` (asserted by the tests).

Limitations: this models the event flow only; it is not ADK, an A2A SDK or a session service, and the `append` flag on client events is the model's own convention. Check ADK release notes for the follow-up that re-lands aggregation behind a setting. Views are my own and do not represent any employer, past or present.
