# google-genai 3.0.0: pin the API version and HTTP client your code uses

**Author: Sandeep Belgavi**

A runnable companion to *google-genai 3.0.0 for Python: v1 by Default, httpx2 and What Breaks on Upgrade*
(aicassindra.com, LLM). Eight offline tests pin what google-genai 3.0.0 does: Gemini Developer API requests go to
`/v1/`, `GOOGLE_GENAI_API_VERSION=beta` restores `/v1beta/`, an explicit `api_version` in code wins over the
environment, `caches.create` is sent to `/v1/cachedContents` without any client-side warning (context caching is
listed as v1beta only in Google's API versions page), an explicit `v1beta` client sends it to
`/v1beta/cachedContents`, Vertex AI clients keep `v1beta1`, and the default HTTP client is httpx2.

**No request leaves the machine.** A placeholder key and an `httpx2.MockTransport` record the request paths; the
mock answers cache calls with 404, so these tests say nothing about how the real API responds.

## Prerequisites

- Python 3.11 or newer.
- `pip install -r requirements.txt` (google-genai 3.0.0, which brings httpx2 and truststore). Use a fresh virtual
  environment; google-adk 2.13.0 requires google-genai below 3, so do not install this next to ADK.
- `.env.example` documents that nothing is read from the environment and that no real key is needed.

## Commands

```
python -m venv .venv && .venv/Scripts/python -m pip install -r examples/python/genai_v1_upgrade_check/requirements.txt
.venv/Scripts/python -m unittest discover -s examples/python/genai_v1_upgrade_check -p "test_*.py"
```

(On macOS or Linux use `.venv/bin/python`.)

## Expected output

`Ran 8 tests ... OK` with google-genai 3.0.0. With 2.34.0 installed, the version, default-path and HTTP-client
tests fail, which is the point: the suite records the version your code was reviewed against.

## Limitations

The tests read two private attributes (`_api_client._http_options` and `_httpx_client`) to check the Vertex
default and the client class; they may change in a later SDK release. Keep a reference to each `Client` while you
use it: calling a method on an unnamed temporary client failed in our runs with `Cannot send a request, as the
client has been closed`.
