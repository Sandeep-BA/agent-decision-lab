# Flaky agent evaluation cases: harness bugs versus model variance

**Author: Sandeep Belgavi**

A runnable companion to *Flaky Agent Evaluation Cases: Harness Bugs Versus Model Variance* (aicassindra.com,
Agents). It plants three harness faults from the article in the fictional Belgavi's Book Store help-desk suite
(a real clock in CASE-6001's return-window check, a tool that returns a set, two cases sharing one sandbox) and
classifies run records: anything that varies under replay is the harness; parallel-only variation is shared
state; variation only with a live model is model variance. It also computes how many clean runs are needed to
catch a flake of a given rate and an unbiased pass^k estimate. See also [`eval_noise`](../eval_noise/) for
splitting score variance once the harness is deterministic.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- `.env.example` documents that nothing is read from the environment. Live runs are simulated with a seeded
  sampler; no model is called.

## Commands

```
python examples/python/eval_flake_classifier/flakes.py
python -m unittest discover -s examples/python/eval_flake_classifier -p "test_*.py"
```

## Expected output

```
{"case_6001_real_clock": false, "case_6001_frozen_clock": true}
{"shared_state_case": "shared state", "live_case": "model variance", "runs_needed_5pct": 59, "runs_needed_20pct": 14, "pass_hat_4_of_16_with_12": 0.272}
```

The first line is fixed because the "real clock" is set to 6 November 2026 in the demo. The tests also check the
article's table: 14, 29, 59 and 149 clean runs for 95 percent detection at 20, 10, 5 and 2 percent per-run
failure rates.

## Limitations

The classifier reads run records; recording and replaying model responses is up to your harness. It assumes
replayed runs really remove the model, so a recording that still calls a live tool will be misclassified as a
harness bug, which is usually what it is. The pass^k estimate assumes independent trials.
