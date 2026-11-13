# Write through a handle opened before untrusted work runs

**Author: Sandeep Belgavi**

A runnable companion to *Open the Output File Before the Untrusted Work Runs: Path Swaps, Symlinks and Writing Through a Bound Handle* (aicassindra.com). A reproduction in a temporary directory: untrusted work replaces the output name with a hard link to a settings file, either during the job or before it starts. A late writer that opens the pathname afterwards overwrites the settings file; a bound writer opens first, refuses multiply linked files and checks that the pathname still names the same file before writing.

## Prerequisites

- Python 3.11 or newer. Standard library only.
- `.env.example` documents that nothing secret is read from the environment. No API keys, no network calls beyond loopback.

## Sample input

A synthetic store-settings.conf (refund_limit=50) and result text for CASE-9050.

## Commands

From this directory:

```
python bound_output.py
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Recorded on Windows NTFS: the late writer overwrote the settings file in both attack scenarios. The bound writer kept it intact; with a link planted earlier it refused (2 links); during the job Windows refused to delete the open output file (WinError 32). 7 tests pass.

## Limitations

Symlink swaps were not reproduced here (they need extra privileges on Windows). On Linux use O_NOFOLLOW and the same identity checks; directory-level swaps need openat-style APIs.

Views are my own and do not represent any employer, past or present.
