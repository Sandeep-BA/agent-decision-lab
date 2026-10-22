# Tenant fair queue for agent traffic on a shared service

**Author: Sandeep Belgavi**

A runnable companion to *Agent Traffic on Shared Internal Services: Per-Tenant Fair Queuing, Concurrency
Caps and Re-Plan Amplification* (aicassindra.com, system_design). It contains three small building blocks
and a deterministic scenario that exercises them:

- `FifoAdmission`: one bounded queue for every tenant, the usual starting point;
- `FairAdmission`: one bounded queue per tenant, served round-robin, so a tenant can only fill and wait in
  its own queue;
- `AgentBudget`: a token bucket the agent runtime checks before sending a call, plus a cap on re-plan
  rounds, so failures cannot multiply the agent's own traffic.

`simulate()` runs 120 seconds on a 10 ms clock. A service with 8 workers and 200 ms per call (about 40
calls per second) serves three ordinary tenants at 8 calls per second each and one agent tenant at 8 calls
per second, which rises to 40 per second from 30 s to 70 s. Each refused or abandoned agent call is
re-planned into two new calls half a second later, for at most three rounds. Callers abandon a call that
has waited 2 seconds in the queue.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt`).
- No environment variables or credentials (`.env.example`). Nothing calls a model or a network service.

## Commands

From the repository root:

```sh
python examples/python/tenant_fair_queue/fair_queue.py --policy fifo
python examples/python/tenant_fair_queue/fair_queue.py --policy fair
python examples/python/tenant_fair_queue/fair_queue.py --policy fifo --budget 10
python examples/python/tenant_fair_queue/fair_queue.py --policy fifo --replan 0
python -m unittest discover -s examples/python/tenant_fair_queue -p "test_*.py"
```

## Expected output (verified with Python 3.13)

Each command prints JSON. The key figures:

| Command | Ordinary tenants served | Worst ordinary tenant | Agent calls offered | Agent re-plan calls |
| --- | --- | --- | --- | --- |
| `--policy fifo` | 84.2% | 76.7% | 14,092 | 11,852 |
| `--policy fifo --replan 0` | 88.5% | 84.7% | 2,240 | 0 |
| `--policy fair` | 100.0% | 100.0% | 24,816 | 22,632 |
| `--policy fifo --budget 10` | 100.0% | 100.0% | 1,049 (1,191 held back by the budget) | 0 |

Fair queues protect the ordinary tenants but make the agent's own amplification worse, because more of its
calls are refused and each refusal is re-planned. The budget removes the amplification where it starts.

## Tests

`test_fair_queue.py` (10 tests): a full tenant queue refuses only that tenant; FIFO lets one tenant fill
the shared queue; round-robin alternates between backlogged tenants; expiry removes calls past the wait
limit; the budget refuses calls beyond its bucket and its round limit; and the four scenario figures above,
plus determinism.

## Limits

The scenario is a teaching model: arrivals are evenly spaced, every call takes exactly the same time, the
service never slows down under load, and re-plans always target the same service. Real systems have
variable service times, client retries, connection pools and autoscaling. The interactive lab on
aicassindra.com runs the same model with every input exposed.
