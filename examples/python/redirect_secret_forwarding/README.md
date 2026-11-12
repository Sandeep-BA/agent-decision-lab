# Which secrets a followed redirect delivers

**Author: Sandeep Belgavi**

A runnable companion to *Redirects That Carry Secrets: What Clients Strip on a New Host and What 307 and 308 Resend* (aicassindra.com). A loopback probe (token endpoint on 127.0.0.1 redirecting to a recorder on localhost) for Python requests and Node.js fetch, and an offline one-hop model of Fetch, requests, a copy-everything loop and a no-follow client.

## Prerequisites

- Python 3.11 or newer with `pip install -r requirements.txt` (requests==2.33.1) for the probe; Node.js 18 or newer for the fetch probe. The model and its tests need only the standard library. Loopback only; synthetic secrets.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Synthetic bearer token, X-Api-Key and form body with refresh_token and client_secret in local_probe.py.

## Commands

From this directory:

```
python -m unittest test_redirect_model -v
python local_probe.py
python run_node_probe.py
```

## Expected output

Seven model tests pass. Recorded probe (requests 2.33.1, Node.js 22.17.0): 301, 302 and 303 arrive as GET without the body; 307 and 308 arrive as POST with the body; Authorization never arrives; X-Api-Key always does.

## Limitations

One hop; cookies, proxies, multi-hop chains and other clients are not modelled. Library behaviour can change between versions; rerun the probe on yours.

Views are my own and do not represent any employer, past or present.
