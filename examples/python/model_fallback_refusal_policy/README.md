# Refusal fallback policy: pinning pydantic-ai ModelFallback with tests

**Author: Sandeep Belgavi**

A runnable companion to *pydantic-ai 2.65 Changes How Model Refusals Trigger Automatic Fallback* (aicassindra.com,
agents). The Belgavi's Book Store help desk agent has a primary and a backup model. In pydantic-ai 2.65.0 the
`ModelFallback` default `fallback_on` is `(ModelAPIError, ContentFilterError)`, so a refusal
(`finish_reason="content_filter"`) is sent on to the backup. This example names both policies in code and tests
what each does, so a later library default cannot change the behaviour silently.

**No model is called.** Both models are `FunctionModel` instances returning fixed synthetic responses.

## Prerequisites

- Python 3.11 or newer.
- `pip install -r examples/python/model_fallback_refusal_policy/requirements.txt` (pins `pydantic-ai-slim==2.65.0`).
  A virtual environment is recommended.
- No API key. `.env.example` documents that nothing is read from the environment except the optional banner switch.

## Commands

Run from the repository root.

```
python examples/python/model_fallback_refusal_policy/policy.py
python -m unittest discover -s examples/python/model_fallback_refusal_policy -p "test_*.py"
```

## Expected output

```
pydantic-ai 2.65.0
default       refusal+text  calls=['primary', 'backup'] output='Return label sent for order BK-1044.' error=None
default       refusal empty calls=['primary', 'backup'] output='Return label sent for order BK-1044.' error=None
refusals_stop refusal+text  calls=['primary'] output='I cannot help with that.' error=None
refusals_stop refusal empty calls=['primary'] output=None error=ContentFilterError
ModelQuotaExceededError is a ModelRateLimitError: False
```

Eight unittest cases: the pinned version, both default scenarios, the explicit default tuple, the stop policy never
calling the backup, the stop policy raising on an empty refusal, the stop policy returning refusal text as output,
and quota errors not being rate-limit errors.

## Limitations

- Non-streamed runs only. The library documents that streamed refusals are accepted as they are.
- The Temporal `non_retryable_model_errors` default is not exercised; it needs the `temporal` extra and a Temporal
  test server.
- `FunctionModel` reproduces the response shape, not any provider's actual refusal behaviour or error mapping.
- Under the stop policy a refusal with text becomes the run output. If users must never see that as an answer,
  check `finish_reason` on the final response yourself.
