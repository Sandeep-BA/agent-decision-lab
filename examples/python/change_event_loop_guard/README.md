# Loop guards for agents subscribed to change events

**Author: Sandeep Belgavi**

A runnable companion to *Agents That React to Changes They Caused* (aicassindra.com, System design). Two
catalogue agents for a book shop, a description writer and a tagger, subscribe to product-changed events and
write back to the product. The example shows which guard stops which loop: an origin filter, no-op
suppression, a hop limit, and breaking the data cycle.

**No model or network is called.** The agents are scripted functions; one of them appends a draft counter
to imitate a model whose rewrite differs on every call.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/change_event_loop_guard/loopguard.py
python -m unittest discover -s examples/python/change_event_loop_guard -p "test_*.py"
```

## Expected output

| Scenario | Agent calls | Events | Deepest hop | Result |
| --- | --- | --- | --- | --- |
| `drifting_agent_no_guards` | 500 | 502 | 250 | event budget hit |
| `drifting_agent_origin_filter` | 2 | 4 | 1 | settles |
| `two_agents_origin_filter_only` | 502 | 504 | 126 | event budget hit |
| `two_stable_agents_noop_suppression` | 10 | 8 | 2 | settles, 4 no-op writes skipped |
| `two_agents_hop_limit_backstop` | 16 | 18 | 4 | stopped by the hop limit 4 times |
| `cycle_broken_in_the_data` | 10 | 8 | 2 | settles although the describer drifts |

Seven unittest cases check these outcomes and that every agent write carries a causation id and a hop.

## Limitations

One in-memory queue, two fields per agent and no concurrency. Real loops can pass through other systems
(sync jobs, warehouses) that must propagate the origin and causation fields too.
