# Run leases and epoch fencing for agent tool calls

**Author: Sandeep Belgavi**

A runnable companion to *Zombie Agent Runs: Fencing Tool Calls With a Run Epoch After a Lease Is Reclaimed* (aicassindra.com). A lease table that increments an epoch on every takeover, and a tool server that can reject writes carrying an older epoch. `scenario()` replays one worker pausing past its lease while a second worker resumes the run.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

`scenario()` defaults: TTL 30 s, heartbeat 10 s, pause at 25 s for 60 s, reclaim delay 5 s, new worker writes 20 s after its grant. Run `python fencing.py` to print four variants.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Nine tests pass. Without fencing two refunds are issued for CASE-4107. Fencing on write rejects the expired worker when the new owner wrote first, but not when the expired worker writes first; registering the epoch at takeover rejects it in both orders. An idempotency key alone prevents the second refund but lets the expired worker overwrite the case status.

## Limitations

Whole-second simulated time and a perfectly reliable lease table. It does not model clock drift, network delay on the write itself, or a lock service such as etcd, ZooKeeper or a Kubernetes Lease.

Views are my own and do not represent any employer, past or present.
