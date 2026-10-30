# Cache invalidation when an agent writes around the service

**Author: Sandeep Belgavi**

A runnable companion to *When an Agent Writes Around the Application Cache* (aicassindra.com, System design).
A book shop's catalogue service reads through a cache-aside cache with a 300-second TTL. An agent changes
stock either straight in the database, through the service, or straight in the database with a change-stream
consumer that invalidates the cache. The example also shows the slow-refill race and how a versioned
tombstone refuses it.

**No model, cache server, database or network is called.** The database is a dict with a change log, the
cache is a dict, the clock is an integer, and the agent's write is a scripted call.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/agent_cache_invalidation/cacheinval.py
python -m unittest discover -s examples/python/agent_cache_invalidation -p "test_*.py"
```

## Expected output

```
direct_write                       {'t20': 12, 't299': 12, 't300': 0}
service_write                      {'t20': 0}
change_stream_lag_2s               {'before_consumer': 12, 'after_consumer': 0}
slow_refill_plain_delete           {'refill_stored': True, 't3': 12}
slow_refill_versioned_tombstone    {'refill_stored': False, 't3': 0}
```

`BK-4001` starts with 12 copies; the agent marks it sold out (0). A direct database write leaves the
storefront on 12 until the cached copy expires at 300 seconds. Seven unittest cases check these outcomes,
that a late invalidation never removes a newer entry, and that the consumer covers every writer.

## Limitations

One key, one process and an integer clock. Real caches need the compare-and-set to be atomic (a script or
a transaction in the cache server), real change streams can stop rather than lag, and the tombstone TTL must
be longer than the slowest reader's load time.
