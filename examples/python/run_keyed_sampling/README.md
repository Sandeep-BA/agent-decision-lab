# run_keyed_sampling

**Author: Sandeep Belgavi**

Companion to the guide *Sample Whole Agent Runs, Not Single Traces* on aicassindra.com.

An agent run that waits for an approval, a callback or a resume produces several traces. Sampling each
trace on its own TraceID keeps fragments of runs. This example derives the OpenTelemetry tracestate
explicit randomness value `rv` from the run id, so every trace of a run gets the same consistent
probability sampling decision, and compares the two policies on synthetic runs.

- `sampling.py`: the rejection threshold `T = (1 - p) * 2^56`, the `R >= T` decision, `rv_for_run()`
  (14 lower-case hex digits from SHA-256 of the run id) and a deterministic replay over synthetic runs.
- `demo.py`: 2,000 synthetic runs with one to four traces each.

## Prerequisites

Python 3.11 or newer, standard library only. Tested with Python 3.13.5. No collector or SDK is needed:
the example computes decisions; it does not export spans.

## Run

```
python demo.py
python -m unittest -v
```

Expected output (`expected_output.txt`):

```
runs 2000, traces 5081, runs with more than one trace 1500
threshold for p=0.1: e6666666666666
tracestate for run-00042: ot=rv:8a84c66f6e2dda
p=0.10 trace kept whole   51  partial  389  dropped 1560  traces kept  485 of 5081
p=0.10 run   kept whole  203  partial    0  dropped 1797  traces kept  530 of 5081
p=0.25 trace kept whole  161  partial  811  dropped 1028  traces kept 1247 of 5081
p=0.25 run   kept whole  504  partial    0  dropped 1496  traces kept 1279 of 5081
```

## Using it with an SDK

The OpenTelemetry specification lets a root span carry `tracestate: ot=rv:<value>` and requires samplers
not to overwrite it, so set it from `rv_for_run(run_id)` for every trace that belongs to the run (the
first request, each resume, each callback) and use a sampler that reads explicit randomness, such as the
ProbabilitySampler. SDK support varies and was not tested here. In many SDKs the only way to give a root
span a tracestate is a remote parent context, and a ParentBased sampler then follows that parent's sampled
flag instead of calling the root sampler, so compute the decision with `keep()` and set the flag yourself,
or check how your SDK handles it. The deprecated TraceIdRatioBased sampler decides from the TraceID, not `rv`.

## Limitations

- Synthetic TraceIDs and run lengths; decisions are exact, volumes are illustrative.
- `rv` must be close to uniformly random for the kept share to match `p`. A cryptographic hash of a
  unique run id is; a sequence number is not.
- Anyone who knows a run id can compute its `rv`, so `rv` decides sampling only, never access. Do not
  derive it from secrets or personal data.
- Tail sampling that decides per trace can still split a run. Keeping a whole run because one of its
  traces failed needs a decision store keyed by run id, which this example does not implement.
