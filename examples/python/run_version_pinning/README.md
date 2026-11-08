# Resuming an agent run across deploys

**Author: Sandeep Belgavi**

Companion to *A Resumed Agent Run Meets New Code*. `resume.py` holds the deterministic resume decision: pin, migrate or close out.

## Prerequisites
Python 3.11 or newer; standard library only.

## Commands
```
python examples/python/run_version_pinning/resume.py examples/python/run_version_pinning/fixtures/runs.json
python -m unittest discover -s examples/python/run_version_pinning -p "test_*.py"
```

## Expected output
```
CASE-6133 Thursday pin bundle agent-2026.11.2 is still deployed
CASE-6133 three weeks later migrate migration 3->4 exists
CASE-5901 very old close_out no live bundle and no migration for schema 2
```

## Limits
The routing of a resumed run to the right worker and the migration functions themselves are outside this example.
