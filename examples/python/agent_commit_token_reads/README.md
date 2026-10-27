# Commit tokens in tool results: verifying an agent's write against a lagging replica

**Author: Sandeep Belgavi**

A runnable companion to *When an Agent Checks Its Own Write: Replica Lag, Commit Tokens in Tool Results and
Duplicate Actions From Stale Verification* (aicassindra.com, System design). A scripted agent issues a refund
for CASE-4182, reads the order back through a replica, and issues the refund again if the read shows none.
The store keeps a commit log; the replica applies it after a configurable lag.

**No model or database is called.** The agent is a fixed script and time is simulated, so the guards can be
tested exactly.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/agent_commit_token_reads/tokens.py 2.1        # one JSON line per scenario, lag 2.1 s
python -m unittest discover -s examples/python/agent_commit_token_reads -p "test_*.py"
```

## Expected output (lag 2.1 s)

| Scenario | Refunds issued | Agent believes the first refund failed | Verification read |
| --- | --- | --- | --- |
| `no_guards` | 2 | yes | replica, `none` |
| `commit_token` | 1 | no | waits 0.5 s, then the primary returns `R1` |
| `freshness_flag` | 1 | no | replica, `unknown`, `fresh: false` |
| `intent_key` | 1 | yes | replica, `none`; the second call is a no-op |
| `all_guards` | 1 | no | primary, `R1` |

With a lag of 0.6 s the token-guarded read waits 0.25 s and is served by the replica. The tests cover all of
these cases plus the no-lag case.

## Limitations

The replica applies writes exactly `lag` seconds after commit, the wait polls in 50 ms steps of simulated time,
and the agent is a three-step script. Real replicas lag unevenly, real tokens are LSNs or GTID sets, and a real
fallback to the primary needs a limit so that a replication incident does not overload it.
