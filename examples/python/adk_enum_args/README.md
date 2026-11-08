# Enum arguments in ADK Python 2.14

**Author: Sandeep Belgavi**

Companion to *ADK Python 2.14: Enum Tool Arguments Become Members*.

## Prerequisites
Python 3.11 or newer. `parse_reason` and its tests need nothing else. For the framework test, in a fresh virtual environment, `pip install -r examples/python/adk_enum_args/requirements.txt`.

## Commands
```
python -m unittest discover -s examples/python/adk_enum_args -p "test_*.py"
python examples/python/adk_enum_args/enum_args.py
```

## Expected output
On google-adk 2.14.0: `{'case_id': 'CASE-6101', 'reason_type': 'Reason', 'reason_eq': False, 'channel_eq': True}`.
On 2.13.0 `reason_type` is `str` and `reason_eq` is `True`.

## Limits
Calls the tool directly through `FunctionTool.run_async`, without a real model.
