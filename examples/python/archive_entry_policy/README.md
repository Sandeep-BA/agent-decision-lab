# Whole-archive entry policy

**Author: Sandeep Belgavi**

A runnable companion to *Duplicate Archive Entries Can Defeat an Early Image Validation Check* (aicassindra.com). A metadata-only validator that must see every entry before accepting an archive.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no database server, no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

Name and type pairs written in the tests. No archive is opened and nothing is extracted.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Two tests pass. A plain tree is accepted. A later duplicate `rootfs` symlink, an absolute path, a parent traversal, a device entry and two names that normalize alike are all rejected.

## Limitations

This is a policy exercise, not an extraction library. It does not model extended headers, Unicode equivalence, filesystem races, resource limits or any real extractor.

Views are my own and do not represent any employer, past or present.
