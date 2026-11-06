# Limits before work: JSON indentation growth and a bounded formatter

**Author: Sandeep Belgavi**

A runnable companion to *pydantic-ai 2.66.0: Ten Advisories, Most About Work Done Before a Limit*
(aicassindra.com, Security). GHSA-m5vj-8mcw-82qx describes a web-fetch tool that pretty-printed JSON before
applying its content limit. `bounded.py` measures why that matters with Python's own `json` module, where the
indented size grows with nesting depth, and shows a formatter that checks size and depth with a linear scan
before doing any expensive work.

**This is not pydantic-ai code** and does not reproduce the advisory's code path. It illustrates the pattern.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- `.env.example` documents that nothing is read from the environment. No network is used.

## Commands

```
python examples/python/bounded_json_format/bounded.py
python -m unittest discover -s examples/python/bounded_json_format -p "test_*.py"
```

## Expected output

```
{"depth": 500, "leaves": 0, "raw_bytes": 1000, "indented_bytes": 500000, "compact_bytes": 1000, "growth": 500}
{"depth": 900, "leaves": 0, "raw_bytes": 1800, "indented_bytes": 1620000, "compact_bytes": 1800, "growth": 900}
{"depth": 400, "leaves": 100000, "raw_bytes": 200799, "indented_bytes": 80620798, "compact_bytes": 300798, "growth": 401}
```

The sizes are deterministic for CPython's `json` with `indent=2`. The last case builds an 80 MB string in memory.

## Limitations

Python's `json` parser raises `RecursionError` at around the interpreter's recursion limit (1000 by default), so
very deep documents fail during parsing rather than formatting; the depth check refuses them earlier with a clear
error. The scan handles strings and escapes but does not validate JSON; parsing still does that. Choose limits for
your own tools; 200,000 bytes and depth 64 are examples.
