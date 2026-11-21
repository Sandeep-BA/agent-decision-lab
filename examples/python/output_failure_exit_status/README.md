# Make output failures reach the exit status

**Author: Sandeep Belgavi**

A runnable companion to *Make Agent Output Failures Reach the Process Exit Status* (aicassindra.com). Runs three writers as real child processes against a simulated full disk (a raw stream that raises ENOSPC after a byte budget, under the standard BufferedWriter): one swallows errors, one writes its DONE marker before closing, one writes to a temporary name, flushes, closes, renames and only then writes the marker. Also measures the interpreter exit status when buffered stdout cannot be flushed at exit.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13.5 on Windows). Standard library only.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

200 synthetic refund cases; the JSON payload is 16,846 bytes.

## Commands

From this directory:

```
python run_matrix.py
python -m unittest -v
```

## Expected output

Swallow: exit 0 with a marker and a broken summary at budgets 4096 and 16746. Marker first at 16746: exit 1 but the marker exists. Checked: exit 1, no marker, `error: summary not written` on stderr. Buffered stdout that cannot be flushed at exit: status 120, `OSError: [Errno 22] Invalid argument` on Windows. 5 tests pass.

## Limitations

The full disk is simulated in user space; a real filesystem can also report errors only at fsync, or (NFS) later still. Not a test of any specific CLI.

Views are my own and do not represent any employer, past or present.
