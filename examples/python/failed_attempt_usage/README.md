# Count usage from failed and incomplete attempts

**Author: Sandeep Belgavi**

A runnable companion to *OpenAI Agents SDK 0.25.0 Counts Tokens From Failed and Incomplete Attempts* (aicassindra.com). One model call takes three physical attempts: incomplete with reported usage, a connection reset with none, then success. The example compares success-only accounting, per-attempt accounting keyed by attempt number (the behaviour openai-agents-python 0.25.0 describes), a double-counting bug and a budget check.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

`ATTEMPTS` in `ledger.py`; the first attempt uses the 12 input and 16 output tokens from the SDK's own regression test.

## Commands

From this directory:

```
python ledger.py
python -m unittest -v
```

## Expected output

Success only: 3 requests, 36 tokens. Per attempt: 3 requests, 64 tokens, 1 attempt with no reported usage. Double counting: 92. Two incomplete attempts with no success: 0 tokens before, 58 after. A 60-token budget continues on the old ledger and stops on the new one. 6 tests pass.

## Limitations

A standalone model; it does not import the SDK or call a provider. Provider billing is authoritative; reconcile against it rather than treating any client-side ledger as the bill.

Views are my own and do not represent any employer, past or present.
