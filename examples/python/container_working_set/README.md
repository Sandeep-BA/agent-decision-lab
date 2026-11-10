# cgroup v2 memory: usage, page cache and working set

**Author: Sandeep Belgavi**

A runnable companion to *Container Memory Working Set: Why Page Cache Shows Up Near Your Limit* (aicassindra.com). Computes working set as memory.current minus inactive_file, as the kubelet documents for eviction, and separates anonymous memory from file cache before calling something an OOM risk.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

`CACHE_HEAVY` and `ANON_HEAVY` memory.stat samples in `working_set.py`; `from_directory()` reads the same three files from a live cgroup directory.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Four tests pass. A 1 GiB-limited container with 950 MiB usage and 40 MiB inactive file cache has a 910 MiB (88.9 percent) working set while anonymous memory is only 29.3 percent of the limit.

## Limitations

The thresholds in `analyse()` are teaching heuristics, not kernel or kubelet behaviour. Reclaim success depends on dirty pages, swap, mlock and other cgroup settings that this script does not model.

Views are my own and do not represent any employer, past or present.
