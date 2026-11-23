# Build-time edge schema fit, modelled after ADK Java 1.15.0

**Author: Sandeep Belgavi**

A runnable companion to *ADK Java 1.15.0 Checks Workflow Edge Schemas When the Graph Is Built* (aicassindra.com). An original Python checker for whether one node's output schema fits the next node's input schema by type, enum, required keys, nullability and closed objects. It follows the rules documented in ADK Java 1.15.0's workflow edge check; it is not a port of that code.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Ten synthetic edges in `schema_fit.py`, from refund records between help-desk workflow nodes.

## Commands

From this directory:

```
python schema_fit.py
python -m unittest -v
```

## Expected output

Fits: integer into number, enum subset, open object with an extra key, map into a record, bounds that differ. Does not fit: number into integer, enum superset, nullable into non-null, extra key into a closed inferred record, missing required key. 7 tests pass.

## Limitations

Covers the subset of schema keywords discussed in the article. Formats, patterns and numeric bounds are ignored, as in ADK Java; values that violate them still fail at run time.

Views are my own and do not represent any employer, past or present.
