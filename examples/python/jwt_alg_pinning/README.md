# Pinning the JWT algorithm

**Author: Sandeep Belgavi**

Companion to *Keycloak JWT Authorization Grant: An HMAC Assertion Checked Against a Public Key*.

## Prerequisites
Python 3.11 or newer; standard library only. Keys are synthetic text, not real key material.

## Commands
```
python examples/python/jwt_alg_pinning/verify.py
python -m unittest discover -s examples/python/jwt_alg_pinning -p "test_*.py"
```

## Expected output
```
vulnerable verifier accepts: {'sub': 'geetha', 'role': 'admin'}
pinned verifier rejects: alg 'HS256', expected 'RS256'
```

## Limits
A teaching model of the algorithm confusion, not a security tool and not Keycloak code. For real tokens use a maintained JOSE library with explicitly allowed algorithms.
