"""Weekly online evaluation of an agent that separates a traffic-mix shift from a quality drop.

Author: Sandeep Belgavi. Companion to the aicassindra.com guide "Online Evaluation of a Production
Agent: Stratified Sampling, a Judge Budget and Telling a Traffic-Mix Shift From a Real Quality
Drop". Standard library only. Runs are synthetic; the judge label is part of the fixture, so no
model is called.

Commands (from the repository root):
  python examples/python/online_eval_mix_shift/online_eval.py --week hidden-regression --allocation uniform
  python examples/python/online_eval_mix_shift/online_eval.py --week hidden-regression --allocation equal
  python examples/python/online_eval_mix_shift/online_eval.py --week mix-shift --allocation equal
"""
import argparse
import json
import random
from math import sqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCENARIOS = json.loads((HERE / "fixtures" / "scenarios.json").read_text(encoding="utf-8"))
SEGMENTS = ("billing", "account", "technical")


def wilson(passed, n, z=1.96):
    """95% Wilson score interval for a pass rate."""
    if n == 0:
        return (0.0, 1.0)
    p = passed / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (centre - half, centre + half)


def make_runs(week, n, seed):
    """Synthetic finished runs: segment assigned at write time, judged pass label attached."""
    rng = random.Random(seed)
    runs = []
    for i in range(n):
        seg = rng.choices(SEGMENTS, weights=[week["mix"][s] for s in SEGMENTS])[0]
        runs.append({"run_id": "r%05d" % i, "segment": seg, "judge_pass": rng.random() < week["rates"][seg]})
    return runs


def allocate(counts, budget, how, baseline):
    """Judged runs per segment: uniform (by traffic), equal, or Neyman (traffic x sd at baseline)."""
    total = sum(counts.values())
    if how == "uniform":
        weights = {s: counts[s] / total for s in SEGMENTS}
    elif how == "equal":
        live = [s for s in SEGMENTS if counts[s]]
        weights = {s: (1 / len(live) if counts[s] else 0) for s in SEGMENTS}
    elif how == "neyman":
        raw = {s: counts[s] * sqrt(baseline[s] * (1 - baseline[s])) for s in SEGMENTS}
        weights = {s: raw[s] / sum(raw.values()) for s in SEGMENTS}
    else:
        raise ValueError("unknown allocation " + how)
    return {s: min(counts[s], round(budget * weights[s])) for s in SEGMENTS}


def weekly_report(runs, budget, how, reference, seed):
    """Stratified sample with a fixed seed, per-segment Wilson intervals, reweighted aggregate."""
    rng = random.Random(seed)
    by_seg = {s: [r for r in runs if r["segment"] == s] for s in SEGMENTS}
    counts = {s: len(by_seg[s]) for s in SEGMENTS}
    quota = allocate(counts, budget, how, reference["rates"])
    mix = {s: counts[s] / len(runs) for s in SEGMENTS}
    rows, aggregate, reweighted = [], 0.0, 0.0
    for s in SEGMENTS:
        sample = rng.sample(by_seg[s], quota[s])
        passed = sum(r["judge_pass"] for r in sample)
        n = len(sample)
        rate = passed / n if n else 0.0
        low, high = wilson(passed, n)
        alert = n > 0 and high < reference["rates"][s]
        rows.append({"segment": s, "share": round(mix[s], 3), "judged": n, "passed": passed,
                     "rate": round(rate, 3), "low": round(low, 3), "high": round(high, 3), "alert": alert})
        aggregate += mix[s] * rate
        reweighted += reference["mix"][s] * rate
    base_agg = sum(reference["mix"][s] * reference["rates"][s] for s in SEGMENTS)
    return {"rows": rows, "mix": {s: round(mix[s], 3) for s in SEGMENTS}, "aggregate": round(aggregate, 3),
            "reweighted": round(reweighted, 3), "baseline_aggregate": round(base_agg, 3)}


def decompose(reference, week):
    """Split the true aggregate change into a mix effect and a rate effect (points)."""
    mix_effect = sum((week["mix"][s] - reference["mix"][s]) * reference["rates"][s] for s in SEGMENTS)
    rate_effect = sum(week["mix"][s] * (week["rates"][s] - reference["rates"][s]) for s in SEGMENTS)
    return round(mix_effect * 100, 1), round(rate_effect * 100, 1)


def aggregate_alert(report, tolerance_points=2.0):
    return (report["baseline_aggregate"] - report["aggregate"]) * 100 > tolerance_points


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--week", choices=sorted(SCENARIOS["weeks"]), default="hidden-regression")
    ap.add_argument("--allocation", choices=["uniform", "equal", "neyman"], default="uniform")
    ap.add_argument("--budget", type=int, default=600)
    ap.add_argument("--seed", type=int, default=20261020)
    args = ap.parse_args()
    ref, week = SCENARIOS["reference"], SCENARIOS["weeks"][args.week]
    runs = make_runs(week, SCENARIOS["runs_per_week"], args.seed)
    rep = weekly_report(runs, args.budget, args.allocation, ref, args.seed + 1)
    mix_eff, rate_eff = decompose(ref, week)
    print("week=%s allocation=%s budget=%d runs=%d" % (args.week, args.allocation, args.budget, len(runs)))
    for r in rep["rows"]:
        print("  %-9s share=%.3f judged=%3d passed=%3d rate=%.3f interval=[%.3f, %.3f] baseline=%.2f alert=%s"
              % (r["segment"], r["share"], r["judged"], r["passed"], r["rate"], r["low"], r["high"], ref["rates"][r["segment"]], r["alert"]))
    print("aggregate=%.3f (reference %.3f) aggregate_alert=%s reweighted=%.3f" % (rep["aggregate"], rep["baseline_aggregate"], aggregate_alert(rep), rep["reweighted"]))
    print("true change split: mix_effect=%+.1f rate_effect=%+.1f points" % (mix_eff, rate_eff))


if __name__ == "__main__":
    main()
