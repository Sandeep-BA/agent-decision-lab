# Mine Agent Traces for the Paths Runs Actually Take Before Keeping the Loop

Author: **Sandeep Belgavi**.

Original teaching example for https://aicassindra.com/blogs/system_design/agent_trace_path_mining_fixed_workflow.html.

`example.py` generates 400 synthetic help-desk runs (CASE-5000 onward) whose `execute_tool` spans are recorded in order, collapses immediate repeats (retries), counts tool-call variants, and for each case kind finds the smallest set of case attributes that decides the path with at least 90 percent purity. Groups that decide the path and carry at least 5 percent of traffic become a compiled workflow; everything else stays with the agent. It then replays the compiled workflow against the recorded runs.

Prerequisites: CPython 3.11 or newer (recorded with 3.13.5 on Windows 11). Standard library only; `requirements.txt` is intentionally empty and `.env.example` documents that nothing is read from the environment. No network, no credentials and no model call.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json` (400 runs, 49 normalized variants, 86.5 percent of runs owned by the compiled workflow, 97.1 percent of those matching the recorded path, 54 runs left to the agent).

Limitations: the traces are generated, so the purity numbers describe the fixture, not any real agent. Only immediate repeats are treated as retries, and only two attributes are searched. Views are my own and do not represent any employer, past or present.
