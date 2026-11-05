# pydantic 2.14.2: extra-data validation fixes and the JSON key-matching change

**Author: Sandeep Belgavi**

A runnable companion to *pydantic 2.14.2 Fixes Two Validation Bypasses in Extra Data, and Changes JSON Parsing*
(aicassindra.com, Security). It reproduces both advisories fixed in pydantic 2.14.2 (released 29 October 2026)
and the release-note behaviour change, with synthetic Belgavi's Book Store tool arguments:

- [GHSA-qpmf-fgh3-ff25](https://github.com/pydantic/pydantic/security/advisories/GHSA-qpmf-fgh3-ff25): extra keys
  skipped their declared key type in JSON mode (2.13.0 up to, but not including, 2.14.2).
- [GHSA-3r8g-cqwr-jr29](https://github.com/pydantic/pydantic/security/advisories/GHSA-3r8g-cqwr-jr29): for TypedDict
  and dataclasses with extra allowed, the field name overrode the validated alias value (up to 2.14.1).
- JSON keys that match only an unused field name are now extra data, as in Python mode.

**No model is called.** The payloads are fixed strings.

## Prerequisites

- Python 3.11 or newer (recorded with CPython 3.13.5 on Windows).
- One pinned environment per version: `requirements-2.13.5.txt`, `requirements-2.14.1.txt`,
  `requirements-2.14.2.txt` (also `requirements.txt`). Each pins pydantic and pydantic-core together.
- No network after installation and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python -m venv .venv-2.14.1
.venv-2.14.1/Scripts/python -m pip install -r examples/python/pydantic_2_14_2_extras/requirements-2.14.1.txt
.venv-2.14.1/Scripts/python examples/python/pydantic_2_14_2_extras/repro.py
.venv-2.14.1/Scripts/python -m unittest discover -s examples/python/pydantic_2_14_2_extras -p "test_*.py"
```

Repeat with the 2.13.5 and 2.14.2 files (on Linux and macOS use `.venv-2.14.1/bin/python`). The tests read the
installed version and assert the behaviour documented for it, so the same suite passes in each environment and
shows the change; they also compare with `expected_<version>.json` when that file exists.

## Expected output

| Check | 2.13.5 | 2.14.1 | 2.14.2 |
| --- | --- | --- | --- |
| JSON extra key `refund_override` against pattern `^x_` | accepted | accepted | string_pattern_mismatch |
| TypedDict `{"refundAmount": 1200, "amount": 999999}`, le=5000 | amount 999999 | amount 999999 | amount 1200 |
| Dataclass, same input | 999999 | 999999 | 1200 |
| BaseModel, same input | 1200 | 1200 | 1200 |
| `{"page_size": 50}` to a camelCase, extra-forbid model, JSON mode | page_size 10 | page_size 10 | extra_forbidden |
| Same with extra allow, JSON mode: extras | `{}` | `{}` | `{'page_size': 50}` |

## Limitations

The reproduction covers the specific shapes described in the advisories and release notes, not every affected
configuration, and it was recorded on one platform. It demonstrates behaviour; it is not a scanner for your code
base. Upgrade decisions should follow the advisories and your own replay of real payloads.
