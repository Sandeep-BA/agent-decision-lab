# Empty versus unset in ${VAR:-default} and ${VAR-default}

**Author: Sandeep Belgavi**

A runnable companion to *Empty Versus Unset: VAR:-default and VAR-default Across Shells, Compose and Config Loaders* (aicassindra.com). An expander for the six POSIX/Compose operators with unset, empty and set variables, a colon-ignoring variant that reproduces the common loader bug, and a cross-check against sh.

## Prerequisites

- Python 3.11 or newer. Standard library only. The sh cross-check runs when `sh` is on the PATH (tested with GNU bash 5.2 as sh) and is skipped otherwise.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

`CASES` and `FORMS` in envsubst.py. `python envsubst.py` prints the table.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Eight tests pass (one skipped if sh is missing). With API_BASE empty, ${API_BASE:-D} gives D and ${API_BASE-D} gives the empty string; the colon-ignoring variant gives the empty string for both.

## Limitations

No nested defaults, no := assignment, no other shell expansions.

Views are my own and do not represent any employer, past or present.
