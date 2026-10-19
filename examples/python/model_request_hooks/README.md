# Model request hooks

**Author: Sandeep Belgavi**

An observation-only hook handler and a metrics aggregator for the harness events described
in *Observation-Only Hooks Around Model Requests* (aicassindra.com, agents). The handler
reads one JSON event on standard input, pairs `PreModelRequest` with `PostModelRequest` on
the turn id, appends one record per attempt to a JSON Lines file, and never writes anything
to standard output. The aggregator turns that file into attempts per turn, latency and
token totals per model, and failure and cancellation rates.

The event shape follows the `model-request.command.input` schema introduced in the Codex
repository on 18 October 2026 (session id, turn id, cwd, transcript path, model, optional
agent id and type, and on post events a status, error and token usage). Any harness that
emits the same fields can use it; the fixtures are synthetic.

## Prerequisites

- Python 3.11 or newer. Standard library only.
- No network, no provider calls. `.env.example` lists the state directory variable.

## Commands

From the repository root:

```sh
export HOOK_STATE_DIR=/tmp/model-request-hook     # or set it in your hooks configuration
python examples/python/model_request_hooks/hook_observer.py < examples/python/model_request_hooks/fixtures/pre.json
python examples/python/model_request_hooks/hook_observer.py < examples/python/model_request_hooks/fixtures/post.json
python examples/python/model_request_hooks/metrics.py "$HOOK_STATE_DIR/requests.jsonl"
python -m unittest discover -s examples/python/model_request_hooks -p "test_*.py"
```

To register it in a harness that supports these events, add the script as a command
handler for both `PreModelRequest` and `PostModelRequest`. Keep it asynchronous unless you
need the audit ordering described in the guide.

## Sample input and expected output

`fixtures/pre.json` and `fixtures/post.json` are one synthetic attempt for turn `t-7`.
After both commands, `requests.jsonl` holds one line and the aggregator prints:

```
turns=1 attempts=1 attempts_per_turn=1.00
model=example-model-1 attempts=1 completed=1 failed=0 cancelled=0 input_tokens=1200 output_tokens=85 mean_latency_s=<seconds between the two commands>
```

Latency is measured from the pre event marker and is omitted when the marker is missing.
The handler prints its record to standard error only; standard output stays empty by design.

## Tests

`test_hooks.py` checks that: a pre event writes a marker and nothing else; a post event
produces one record with the status, model, agent type and usage; a post event with null
usage records unknown rather than zero; a control-looking directive printed to stdout
never happens (stdout is empty); and the aggregator counts attempts separately from turns
for a retried turn.

## Limitations

- The handler keeps per-turn markers as files; a long-running harness should prune them.
- Pairing is on the turn id; two overlapping attempts in one turn share a marker, so
  per-attempt latency is approximate under concurrency.
- This is a teaching example of the observation contract, not a metrics product.
