# Batch submission ledger for provider batch APIs

**Author: Sandeep Belgavi**

A runnable companion to *Moving Deferrable Agent Work to Provider Batch APIs: What Can Wait, a Submission
Ledger, Partial Results, Expiry and Resubmission* (aicassindra.com, llm). The ledger, not the provider, owns
the state of every work item:

- items are chunked into batches under a request-count limit and a byte limit;
- each request carries a `custom_id` of the form `<item>-a<attempt>`, which fits the strictest documented
  format (`^[a-zA-Z0-9_-]{1,64}$`) and never collides across resubmissions;
- results are matched by `custom_id` only, because providers document that output order may differ from
  input order;
- expired, canceled and missing requests go back to pending until a maximum number of attempts; invalid
  requests go to human review and are never resubmitted;
- reconciling the same results twice changes nothing, and a late result of an earlier attempt is ignored.

`FakeProvider` simulates the end-of-window behaviour that the three providers document differently: an
OpenAI-style batch returns finished requests plus `batch_expired` errors, an Anthropic-style batch reports a
result type per request, and a Gemini-style job that runs past 48 hours expires with no results at all.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install.
- No provider is called and no credentials are read (`.env.example`). The simulation says nothing about real
  provider latency, completion rates or prices.

## Commands

From the repository root:

```sh
python examples/python/batch_submission_ledger/ledger.py --provider openai
python examples/python/batch_submission_ledger/ledger.py --provider anthropic
python examples/python/batch_submission_ledger/ledger.py --provider gemini
python -m unittest discover -s examples/python/batch_submission_ledger -p "test_*.py"
```

Option `--finish` (default 0.5) sets the share of the first batch that completes before its window closes.

## Expected output (verified with Python 3.13)

Twelve tickets, at most five requests per batch, ticket 7 is an invalid request. Summaries of the JSON output:

| Provider style | Round results (succeeded / retried / review) | Final states | Attempts |
| --- | --- | --- | --- |
| openai | 2/3/0, 4/0/1, 2/0/0, 3/0/0 | 11 done, 1 review | 15 |
| anthropic | 2/3/0, 4/0/1, 2/0/0, 3/0/0 | 11 done, 1 review | 15 |
| gemini | 0/5/0, 4/0/1, 2/0/0, 5/0/0 | 11 done, 1 review | 17 |

With partial results only the three unfinished requests are resubmitted; when the whole job expires all five
are.

## Tests

`test_ledger.py` (9 tests): matching by `custom_id` with shuffled results; batch plans respect both limits;
the invalid request ends in review and 11 results are applied; partial expiry resubmits three requests (15
attempts); whole-job expiry resubmits five (17 attempts); reconciling twice is a no-op; a late result of an
earlier attempt is not applied; custom ids match the documented pattern; repeated expiry ends in review.

## Limitations

- The provider is simulated. Real batch APIs have their own request formats, file uploads, polling, result
  retention periods and quotas; read their documentation before adapting the adapter layer.
- A late success of an earlier attempt is ignored here to keep accounting simple; in production you may
  prefer to accept it and cancel the newer attempt, because both are billed.
- The downstream store is a dictionary. Apply results inside a transaction keyed by item id.
