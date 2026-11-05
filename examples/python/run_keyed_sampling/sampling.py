"""Keep or drop every trace of an agent run together.

Author: Sandeep Belgavi.

An agent run that pauses for approval, waits on a callback or resumes after a crash produces
several traces. A sampler that decides per trace (from TraceID randomness) keeps some of a run's
traces and drops others. OpenTelemetry's consistent probability sampling compares a 56-bit
randomness value R with a rejection threshold T and keeps the span when R >= T. R is normally the
trailing 7 bytes of the TraceID, but a root span may carry an explicit value in the OpenTelemetry
tracestate `rv` sub-key (14 lower-case hex digits), which samplers must not overwrite. Deriving
`rv` from the run id makes every trace of the run get the same decision at the same probability.
"""
from __future__ import annotations

import hashlib
from fractions import Fraction

MAX56 = 1 << 56


def threshold(probability: float) -> int:
    """Rejection threshold T = (1 - p) * 2**56, as in the OpenTelemetry specification."""
    if not 2 ** -56 <= probability <= 1:
        raise ValueError('probability must be in [2**-56, 1]')
    return round((1 - Fraction(repr(probability))) * MAX56)   # exact decimal, then round


def keep(randomness: int, probability: float) -> bool:
    return randomness >= threshold(probability)


def trace_randomness(trace_id_hex: str) -> int:
    """The trailing 56 bits of a 128-bit TraceID."""
    return int(trace_id_hex[-14:], 16)


def rv_for_run(run_id: str) -> str:
    """Explicit randomness for every root span of a run: 14 hex digits from a hash of the run id."""
    return hashlib.sha256(run_id.encode('utf-8')).hexdigest()[:14]


def tracestate_for_run(run_id: str) -> str:
    return 'ot=rv:' + rv_for_run(run_id)


def synthetic_trace_id(run_id: str, index: int) -> str:
    """Deterministic stand-in for a random 128-bit TraceID, so the experiment is repeatable."""
    return hashlib.sha256(('%s/trace/%d' % (run_id, index)).encode('utf-8')).hexdigest()[:32]


def synthetic_runs(count: int, max_resumes: int = 3):
    """Run ids and how many traces each produced (1 + resumes), deterministically."""
    runs = []
    for i in range(count):
        run_id = 'run-%05d' % i
        resumes = int(hashlib.sha256(run_id.encode()).hexdigest()[:2], 16) % (max_resumes + 1)
        runs.append((run_id, 1 + resumes))
    return runs


def sample(runs, probability: float, policy: str):
    """policy 'trace': decide each trace from its TraceID; 'run': decide from rv derived from the run id."""
    kept_whole = partial = dropped = traces_kept = 0
    for run_id, traces in runs:
        if policy == 'trace':
            decisions = [keep(trace_randomness(synthetic_trace_id(run_id, i)), probability) for i in range(traces)]
        elif policy == 'run':
            decisions = [keep(int(rv_for_run(run_id), 16), probability)] * traces
        else:
            raise ValueError('unknown policy')
        traces_kept += sum(decisions)
        if all(decisions):
            kept_whole += 1
        elif any(decisions):
            partial += 1
        else:
            dropped += 1
    return {'runs': len(runs), 'kept_whole': kept_whole, 'partial': partial, 'dropped': dropped,
            'traces': sum(t for _, t in runs), 'traces_kept': traces_kept}
