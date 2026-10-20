# Agent tool contracts

**Author: Sandeep Belgavi**

A runnable model of the test strategy in *Testing a Service Once an Agent Calls It: Consumer
Contracts at the Tool Boundary, Recorded Model Replays, Effect Invariants and What Stays Out of
CI* (aicassindra.com, agents). A `refund_order` tool is the boundary between an agent and a
billing service. The example shows three deterministic test layers that need no model:

1. **Consumer contract.** `fixtures/refund_contract.json` holds the tool definition and five
   interactions imitating calls recorded from a staging agent, including the result fields the
   agent read in its next step and two calls the service correctly rejected. `verify` runs them
   against the provider.
2. **Recorded model replay.** `fixtures/recorded_model_responses.json` maps a hash of each
   normalised model request to its recorded response. The tiny runtime in `run_turn` replays a
   turn exactly; an unrecorded request raises `ReplayMiss` instead of calling a live model.
3. **Effect invariants.** A seeded generator produces agent-like call sequences (retries with
   the same key, re-plans with a fresh key) and checks that refunds never exceed the captured
   amount, shrinking any failure to a minimal sequence.

## Prerequisites

- Python 3.11 or newer. Standard library only (`json`, `hashlib`, `random`, `argparse`,
  `unittest`); `requirements.txt` is intentionally empty of packages.
- No network, no model provider, no credentials. `.env.example` documents that nothing is read
  from the environment.

## Commands

From the repository root:

```sh
python examples/python/agent_tool_contracts/tool_contracts.py verify --provider v1
python examples/python/agent_tool_contracts/tool_contracts.py verify --provider renamed
python examples/python/agent_tool_contracts/tool_contracts.py verify --provider lenient
python examples/python/agent_tool_contracts/tool_contracts.py invariants --handler buggy --seed 7
python examples/python/agent_tool_contracts/tool_contracts.py invariants --handler fixed --seed 7
python examples/python/agent_tool_contracts/tool_contracts.py replay
python -m unittest discover -s examples/python/agent_tool_contracts -p "test_*.py"
```

## Expected output

```
provider=v1 interactions=5 failures=0
provider=renamed interactions=5 failures=2
  i1-full-flow: result no longer carries remaining_refundable
  i3-second-order: result no longer carries remaining_refundable
provider=lenient interactions=5 failures=1
  i4-negative-amount-rejected: result no longer carries error; call that used to be rejected is now accepted
handler=buggy invariant violated after 1 sequences; minimal sequence (2 calls):
  refund_order(o-1, 70, key=o-1:k1)
  refund_order(o-1, 55, key=o-1:k2)
handler=fixed invariant held for 200 generated sequences
replayed turn: tool_result={"amount": 40, "refund_id": "rf-1", "remaining_refundable": 60}
answer: Refunded 40. You can still claim up to 60 on this order.
```

The `renamed` provider is a harmless-looking tidy-up that breaks exactly the two interactions in
which the agent read `remaining_refundable`. The `lenient` provider accepts a negative amount that
the recorded agent call expected to be rejected. The `buggy` handler has no cumulative cap check,
so two refunds for one order under two keys, which a re-planning agent produces, exceed the
captured 100; key deduplication cannot catch that.

## Tests

`test_tool_contracts.py` (10 tests) checks each contract failure precisely, that the replay is
deterministic and that a missing recording fails, that the replay fixture matches the recording
job, that the buggy handler shrinks to a two-call over-refund, that the fixed handler holds for 20
seeds, and that a retry with the same key never creates a second effect.

## Limitations

- The provider is an in-memory class; in a real service run verification against the deployed
  handler and its database, so constraints and transactions are exercised.
- The generator and shrinker are a small stand-in for Hypothesis, which offers far better
  strategies and shrinking; the structure of the test is the same.
- The contract checks presence of fields, required arguments and rejected calls. It does not
  validate full JSON Schema types; use a schema validator for that.
- Nothing here measures whether a model chooses the tool well. That needs a statistical
  evaluation outside CI, as the guide explains.
