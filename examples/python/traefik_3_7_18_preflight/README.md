# Traefik v3.7.18 upgrade preflight (offline model)

**Author: Sandeep Belgavi**

A runnable companion to *Traefik 3.7.18 Upgrade: Dot-Segments With Path Parameters, Per-Host TLS Options and a BasicAuth Limit* (aicassindra.com). A model of `sanitizePath` before and after v3.7.18, applied to your router prefixes next to a model of a backend that strips path parameters, plus checks for BasicAuth passwords over 1024 bytes and `default` TLS option settings that stop applying under the Ingress-NGINX provider.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

Two routers (`/help` public, `/help/admin` behind `staff-auth`) and four request paths in `preflight.py`.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Seven tests pass, including all seven sanitization examples from the Traefik request-path documentation. `/help/..;/help/admin/cases` is routed to the public router before v3.7.18 while the modelled backend resolves it to the admin path; from v3.7.18 it is routed to the admin router.

## Limitations

Written from the migration guide and documentation, not from Traefik source. It is not Traefik and cannot prove how your backend parses paths; replay the same requests against a staging proxy and backend.

Views are my own and do not represent any employer, past or present.
