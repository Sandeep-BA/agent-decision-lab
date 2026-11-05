# Partial updates from an agent: merge patch nulls versus JSON Patch tests

**Author: Sandeep Belgavi**

A runnable companion to *Partial Updates From Agents: Merge Patch Nulls, JSON Patch Tests and Field Masks*
(aicassindra.com, System design). It replays the article's opening case on a synthetic Belgavi's Book Store
customer record: a free-form tool forwards the model's JSON Merge Patch, and a typed tool compiles the model's
intent into RFC 6902 operations with `test` preconditions.

**No model or server is called.** `merge_patch` implements the RFC 7396 pseudocode; `apply_json_patch` implements
the `add`, `remove`, `replace` and `test` operations of RFC 6902, atomically.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/agent_patch_semantics/patches.py examples/python/agent_patch_semantics/fixtures/tanishka.json
python -m unittest discover -s examples/python/agent_patch_semantics -p "test_*.py"
```

## Expected output

`expected_output.json` holds the full output. In short:

| Path | Addresses after | Phone | Consent after the website change |
| --- | --- | --- | --- |
| Model-written merge patch | 1 (two replaced) | deleted by `null` | overwritten to `false` |
| Typed tool, JSON Patch | 3 (one `add` to `/addresses/-`) | kept | kept `true` |
| Typed tool asked to set consent from a stale read | unchanged | kept | `test` fails, whole patch rejected |

The tests also check eight cases from RFC 7396 Appendix A, the RFC 6902 rule that a failing `test` leaves the
document unchanged, and that the typed tool refuses fields outside its allow-list.

## Limitations

The JSON Pointer support covers object members, array indices and `-` only, and `move` and `copy` are not
implemented. There is no HTTP layer: `If-Match`, ETags and status codes such as 409 and 412 are described in the
article but not exercised here. The record and the model output are synthetic.
