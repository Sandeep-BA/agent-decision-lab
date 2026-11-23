# Tolerant reader between a service and an agent tool

**Author: Sandeep Belgavi**

A runnable companion to *Let Agent Tools Read Service Responses as Tolerant Readers, Not Strict Mirrors* (aicassindra.com). An order-lookup tool for an agent at the fictional Belgavi's Book Store reads four fields from an order service. A strict mirror of the whole provider schema breaks on additive changes; a tolerant reader validates only consumed fields, ignores unknown ones, maps an unknown status to an explicit `escalate` outcome and counts drift.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Four synthetic payload versions in `reader.py`: v1 unchanged, v2 additive (two new fields and a new status), v3 renamed total, v4 malformed decimal.

## Commands

From this directory:

```
python reader.py
python -m unittest -v
```

## Expected output

v1: both readers return `shipped`. v2: strict fails on `carrier_events`, tolerant returns `escalate` (raw `partially_shipped`). v3: both fail; tolerant names `total.amount` as the missing consumed field. v4: both reject `24,50`. Drift counts: three unknown fields, one unknown status. 6 tests pass.

## Limitations

The consumed-field list is written by hand; a real adapter should derive it from the tool's own output type and export drift counts as metrics. No network calls, no provider schema registry.

Views are my own and do not represent any employer, past or present.
