# Keep UTC Partitions Stable While Reporting Events by Local Day

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/spark/event_date_partitions_utc_local_day.html (article publication pending).

Prerequisites: CPython 3.13.5. No third-party runtime dependencies. The UTC example needs an installed IANA time-zone database; missing zone data is an environment failure, not a passing test.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

The source contains fixed synthetic inputs. `expected.json` records the observed demonstration output after a successful local run. Tests cover failure boundaries and invariants; see `test_example.py` for each fixture.

Limitations: no model, SDK, MCP server or remote system is contacted. This fixture demonstrates its named mechanism only. In-memory workflow and graph examples do not establish database durability, authorization or production recovery. The scheduler has discrete time and cooperative-cancellation assumptions. Token examples establish arithmetic, not billing or latency. Views are my own and do not represent any employer, past or present.
