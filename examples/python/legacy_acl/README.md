# An anti-corruption layer for agent tools over a legacy back office

**Author: Sandeep Belgavi**

A runnable companion to *An Anti-Corruption Layer for Agent Tools Over a Legacy System* (aicassindra.com,
System design). The returns back office of Belgavi's Book Store, faked in memory, has the quirks the article
describes: one-letter status codes where `R` means refunded or rejected depending on an era flag, store
credit stored in points (200 per pound), a reserve/post/release refund sequence, and error codes. The layer
gives agent tools one view type and one idempotent refund operation, and enforces two rules the legacy system
never checked: only open returns are refunded, and refunds never exceed the amount paid.

**No real system, database, model or network is used.**

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` lists nothing to install.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/legacy_acl/acl.py
python -m unittest discover -s examples/python/legacy_acl -p "test_*.py"
```

## Expected output

```
naive_7001                 rejected
layer_7001                 refunded
layer_7002                 rejected
store_credit_pence_7005    800
first_call                 timeout after recording
retry_returns              P1
postings_for_7003          1
rejected_CASE-7004         return is held, not open
rejected_CASE-7003         refund would exceed the amount paid
missing_case               not_found
```

Reading `R` without the era flag calls a refunded return rejected. The first refund call times out after the
back office recorded the posting; the retry with the same idempotency key returns that posting instead of
posting again. Nine unittest cases cover the translations, unknown codes, typed errors, the timeout replay,
hold release, invariants checked before any legacy call, and partial refunds.

## Limitations

The replay check relies on the back office storing the caller reference on postings. If yours cannot, keep
your own table of keys and postings, written in the same transaction as the call log. The fake back office
is single-threaded; concurrent refunds for one case need a lock or a version check in the layer.
