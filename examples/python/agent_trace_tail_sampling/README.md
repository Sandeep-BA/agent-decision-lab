# Tail-Sample Agent Traces by What the Run Did, Then Size the Decision Wait

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/observability/agent_trace_tail_sampling.html.

It simulates 20,000 help-desk agent runs for the fictional Belgavi's Book Store, split into trace segments at durable pauses (approval waits and customer-reply waits), and compares four sampling policies: a 5 percent head sample, outcome rules with a run-level sample bucket, the same rules with a per-trace bucket, and the rules plus keep-every-pre-pause-segment. The rules mirror the OpenTelemetry Collector tail sampling processor policy types (status_code, numeric_attribute, boolean_attribute), evaluated offline.

Prerequisites: CPython 3.11 or newer (tested with 3.13.5). No third-party dependencies (`requirements.txt` is intentionally empty). `.env.example` documents that nothing is read from the environment.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Sample input: generated in `make_runs()` from a fixed seed (26). Expected output: `expected.json` (also asserted by the tests).

Limitations: synthetic runs and rates; no collector, exporter, model or network is involved; memory is estimated as arrival rate times decision window, not measured. The kept percentage depends entirely on how many runs write or need approval in the synthetic mix. Views are my own and do not represent any employer, past or present.
