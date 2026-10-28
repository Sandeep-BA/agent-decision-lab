# 202 Accepted and a job resource for an endpoint that gained an agent step

**Author: Sandeep Belgavi**

A runnable companion to *When an Agent Step Makes a Synchronous Endpoint Too Slow* (aicassindra.com, System
design). A return-assessment endpoint for a book shop answers `POST /return-assessments` with 202, a
`Location` for the job and `Retry-After`, runs a scripted agent in a worker, and keys the store credit on the
return id.

**No model or network is called.** The agent is a fixed function, the database is SQLite in memory, and time
is simulated so the lease can expire on demand.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/async_job_endpoint/jobs.py
python -m unittest discover -s examples/python/async_job_endpoint -p "test_*.py"
```

## Expected output

| Scenario | Jobs | Credits | Final state |
| --- | --- | --- | --- |
| `with_key`: the 202 is lost and the POST is resent with the same Idempotency-Key | 1 | 1 | `succeeded`, amount 20 |
| `without_key`: the same resend with no key | 2 | 1 (the credit is keyed on the return id) | both jobs run |
| `after_crash`: the worker dies after issuing the credit; the lease expires and another worker retries | 1 | 1 | `succeeded`, 2 attempts |

## Limitations

One process plays every role, the lease is checked only when a worker claims, and there is no polling client,
cancel operation or result expiry. A real deployment needs a durable queue, worker heartbeats that renew the
lease, rate limits on the status endpoint and a retention policy for results.
