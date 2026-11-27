# OpenTelemetry Collector Contrib 0.166.0 Makes the Elasticsearch Exporter Retry by Default: Plan for Duplicates

Author: **Sandeep Belgavi**.

Original teaching example for https://aicassindra.com/blogs/observability/otel_elasticsearch_exporter_0_166_retries.html.

`example.py` models the retry defaults documented for the Elasticsearch exporter in v0.165.0 and v0.166.0 against a dictionary store that behaves like the `create` bulk action: a document without an ID gets a generated one, a document whose ID already exists gets 409. Scenarios: a response lost after the bulk was applied, a 503 before anything was applied, document-level 429s and a malformed request.

Prerequisites: CPython 3.11 or newer (recorded with 3.13.5 on Windows 11). Standard library only; `requirements.txt` is intentionally empty and `.env.example` documents that nothing is read from the environment. No network, no credentials and no model call.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json` (a lost response stores 10 documents for 5 records without IDs, and 5 documents plus five 409 reports with deterministic IDs).

Limitations: a model, not Elasticsearch. Data streams, routing, ingest pipelines and the failure store are out of scope. Views are my own and do not represent any employer, past or present.
