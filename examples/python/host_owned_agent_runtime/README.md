# An agent runtime embedded in a host: admission, restricted capabilities, inherited session id

**Author: Sandeep Belgavi**

A runnable companion to *Embedding an Agent Runtime in an Existing Host: Admission, Restricted Capabilities and Inherited Session Identity* (aicassindra.com). A model of a host that owns execution slots (turn admission), marks a thread as restricted from root-only capabilities, and gives a fresh child thread its root session id. Input is recorded before admission so a denial keeps it. Inspired by the shape of three changes in Codex CLI rust-v0.168.0; no Codex code is used.

## Prerequisites

- Python 3.11 or newer. Standard library only.
- `.env.example` documents that nothing secret is read from the environment. No API keys, no network calls beyond loopback.

## Sample input

Synthetic threads thr-jenya-2 and thr-other, session sess-geetha-1 and cases CASE-6120, CASE-6121.

## Commands

From this directory:

```
python host_runtime.py
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

The restricted thread sees only read_case and draft_reply; ask_user is refused. With the single slot held, the first submission is denied and kept; after release both inputs run in order. A cold resume without the marker regains install_plugin; with the marker it is refused. An inherited session id is rejected for a forked thread and when it equals the thread id. 6 tests pass.

## Limitations

Single process, no persistence layer, no real tools or model. Capability names are illustrative.

Views are my own and do not represent any employer, past or present.
