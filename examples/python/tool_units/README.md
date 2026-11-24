# Give Numeric Tool Results Units Before Agents Combine Them

Author: **Sandeep Belgavi**. Original explanation, code and synthetic fixtures.

Normalize typed synthetic duration and byte quantities with dimension checks; reject bare numbers and incompatible arithmetic.

Article destination (publication pending): https://aicassindra.com/blogs/agents/tool_quantity_units_dimension_checks.html

## Prerequisites

CPython 3.13.5. No third-party dependencies; requirements.txt intentionally contains no packages.

## Run from this directory

```text
python example.py
python -m unittest test_example -v
```

Input: `sample-input.json`. Expected output: `expected-output.json`. Tests include negative outcomes, state preservation and boundary cases. All fixtures are synthetic; no provider call occurs.

## Limits

Finite nonnegative decimal duration/data quantities only. No uncertainty model, offset units or measurement.

Views are my own and do not represent any employer, past or present.

## Primary references

- [RFC 8428, August 2018: measurement values and units](https://www.rfc-editor.org/rfc/rfc8428.html)
