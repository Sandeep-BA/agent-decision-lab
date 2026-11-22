# Complete fields in a streamed JSON object

**Author: Sandeep Belgavi**

A runnable companion to *Parse Streamed Model JSON Without Acting on Fields That Are Still Arriving* (aicassindra.com). A scanner reports which top-level fields of a partially received JSON object are certainly finished: strings at their closing quote, objects and arrays at the matching bracket, numbers and literals only once a delimiter follows. A naive preview that closes open strings and brackets and parses is shown beside it.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Five synthetic chunks of a refund proposal for CASE-4201 in `CHUNKS`.

## Commands

From this directory:

```
python fields.py
python -m unittest -v
```

## Expected output

After chunk 1 the preview shows action "ref"; the scanner has only case_id. After chunk 2 the preview shows amount 12; the scanner does not report amount until chunk 3, when it is 125. The items array is not complete until its object closes. The final result equals a full parse, and splitting the 112-character fixture at each of its 111 positions never reports a value that later changes. 7 tests pass.

## Limitations

Top-level fields of one object only; no streaming of nested fields, no JSON Schema validation and no recovery from invalid JSON. Use a maintained incremental parser for production and keep the rule: act only on completed fields, and on the whole object only after the stream ends.

Views are my own and do not represent any employer, past or present.
