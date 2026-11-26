# Keep a Long Agent Loop Inside Durable Workflow History Limits With Continue-As-New

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/system_design/agent_loop_continue_as_new.html.

It estimates how many history events and bytes one agent turn adds to a durable workflow (a customer message as a signal, one model activity, two parallel tool activities), finds which documented Temporal default limit is reached first with the transcript passed inline versus by reference, simulates continue-as-new every 200 turns with carried state, and shows why effect idempotency keys must not be built from the workflow run id.

Prerequisites: CPython 3.11 or newer (tested with 3.13.5). No third-party dependencies (`requirements.txt` is intentionally empty). `.env.example` documents that nothing is read from the environment.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json` (asserted by the tests). Payload sizes are the `Turn` dataclass defaults.

Limitations: event counts per command are an approximation of the scheduled/started/completed pattern; real counts depend on SDK batching, timers and heartbeats. Limits are Temporal's documented defaults (51,200 events / 50 MB, warnings at 10,240 events / 10 MB, 2 MB per payload); other engines differ. No workflow engine, model or network is called. Views are my own and do not represent any employer, past or present.
