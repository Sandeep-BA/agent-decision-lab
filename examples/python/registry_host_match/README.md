# Where may a registry credential go?

**Author: Sandeep Belgavi**

Companion to *A FROM Line That Sent an Entra ID Token to Another Host*. Shows the unanchored check and a fail-safe exact check.

## Prerequisites
Python 3.11 or newer; standard library only.

## Commands
```
python examples/python/registry_host_match/hostmatch.py
python -m unittest discover -s examples/python/registry_host_match -p "test_*.py"
```

## Expected output
```
store.azurecr.io unsafe: True safe: True
store.azurecr.io.attacker.example unsafe: True safe: False
```

## Limits
An illustration, not a kaniko patch. Use the fixed kaniko release for that.
