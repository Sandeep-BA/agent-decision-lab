# Retrieval abstention threshold accounting

**Author: Sandeep Belgavi**

A runnable companion to *A Fixed Similarity Score Cannot Tell You That Retrieval Found Nothing* (aicassindra.com). Counts accepted, false-accepted and covered cases for a candidate score threshold.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no database server, no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

`fixtures.json` holds three synthetic scored cases with independent support labels.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Three tests pass. At threshold 0.8 two cases are accepted, one of them falsely, for precision 0.5.

## Limitations

Scores are synthetic, not model output. Three rows exercise the accounting and cannot establish a production threshold.

Views are my own and do not represent any employer, past or present.
