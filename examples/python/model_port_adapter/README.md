# Model as an adapter: ports and adapters for a returns decision

**Author: Sandeep Belgavi**

A runnable companion to *Ports and Adapters With the Model as an Adapter* (aicassindra.com, System Design).
The returns desk at Belgavi's Book Store decides refunds. The refund rules live in a deterministic domain
function, `decide(order, reading)`. A model is only allowed to fill one port, `CaseReader`, which turns a
customer's message into a typed `Reading` (reason, claimed amount, confidence). Two adapters implement it:
`FixtureReader` (canned readings for tests and the demo) and `ProviderReader` (wraps any callable that returns
JSON text). Every reading passes `validate` at the adapter boundary before the domain sees it.

**No model is called.** `ProviderReader` is exercised only with lambdas in the tests.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` lists nothing to install.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/model_port_adapter/returns.py
python -m unittest discover -s examples/python/model_port_adapter -p "test_*.py"
```

## Expected output

```
CASE-4101  refund        18.50  shop at fault: refund up to the order total
CASE-4102  refund        32.00  shop at fault: refund up to the order total
CASE-4103  deny           0.00  outside the 30-day return window
CASE-4104  review         0.00  low confidence or unclear reason goes to a person
CASE-4105  review         0.00  adapter rejected the model output: unknown reason 'refund_all'
```

Nine unittest cases: five domain tests that use typed readings and no adapter at all (return window, cap at
the order total, low confidence first, repeat refunds, change of mind), and four adapter tests (the demo run,
an unknown reason rejected at the boundary, non-JSON output mapped to review, and the provider adapter
validating exactly like the fixture adapter).

## Limitations

The prompt in `ProviderReader` is a placeholder, not a tuned prompt, and the fixture readings are invented.
The point is the structure: the domain function is the only place a refund rule lives, so rules are tested
without a model and a model swap is an adapter change. Measure the real adapter against labelled cases before
trusting its confidence values.
