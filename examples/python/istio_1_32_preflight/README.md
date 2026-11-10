# Istio 1.32.0 pre-upgrade checks

**Author: Sandeep Belgavi**

A runnable companion to *Istio 1.32 Upgrade: EnvoyFilter Patches That Silently Stop Matching and New API Client Timeouts* (aicassindra.com). Flags gateway EnvoyFilter patches that address `envoy.filters.http.rbac` by name and checks `ISTIO_KUBE_HEADER_TIMEOUT` against the API server request timeout.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

`sample_filter()` in `preflight.py` builds a gateway patch for each operation; feed real objects from `kubectl get envoyfilter -A -o json` after loading them with `json.load`.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Five tests pass: INSERT_BEFORE is reported as dropped and MERGE as no longer applying when ENABLE_GATEWAY_API_HTTPROUTE_AUTH is on; a 45s header timeout under a 60s API server timeout is high severity.

## Limitations

Encodes two items from the 1.32.0 upgrade notes only. It does not parse YAML, contact a cluster or replace istioctl analyze, PILOT_ENVOY_FILTER_STATS and a staging upgrade.

Views are my own and do not represent any employer, past or present.
