"""Forecast the token cost of an agent feature from pilot runs, then check the forecast against week one.

Author: Sandeep Belgavi. Standard library only. No model is called: the pilot and week-one runs are
synthetic fixtures generated from a fixed seed, so every number below is reproducible.

Cost is reported in token counts and in "input-token equivalents": cache reads and cache writes are
weighted by multipliers you take from your provider's price sheet (READ and WRITE below), and output is
weighted by OUTPUT_WEIGHT, the ratio of the output price to the base input price. Multiply by your own
base input price to get money; this example deliberately does not.
"""
import json
import random
import statistics
import sys

PREFIX = 6000        # system prompt and tool definitions, shared by every run
CASE = 800           # the help-desk case text added on step 1
OUT = 300            # output tokens per step
RESULT = 1200        # tool result tokens per step
READ, WRITE = 0.1, 1.25   # illustrative cache multipliers relative to base input
OUTPUT_WEIGHT = 5.0       # illustrative output price divided by base input price


def run_tokens(steps, prefix=PREFIX, case=CASE, out=OUT, result=RESULT):
    """Token usage for one agent run whose context grows by out + result every step.

    Step k sends prefix + case + (k - 1) * (out + result) input tokens. With a warm cache, step 1 reads the
    shared prefix and writes the case; step k > 1 reads everything step k - 1 sent and writes the new turn.
    """
    grow = out + result
    inputs = [prefix + case + (k - 1) * grow for k in range(1, steps + 1)]
    reads = prefix + sum(inputs[:-1])
    writes = case + (steps - 1) * grow
    return {"steps": steps, "input": sum(inputs), "output": steps * out,
            "cache_read": reads, "cache_write": writes}


def equivalents(usage, cached=True):
    """Input-token equivalents: what the run costs in units of one uncached input token."""
    if not cached:
        return usage["input"] + OUTPUT_WEIGHT * usage["output"]
    return READ * usage["cache_read"] + WRITE * usage["cache_write"] + OUTPUT_WEIGHT * usage["output"]


def synthetic_runs(n, seed, mean_steps=7.0, long_share=0.08):
    """Steps per run: mostly short runs plus a share of long investigations (escalations, re-plans)."""
    rnd = random.Random(seed)
    runs = []
    for _ in range(n):
        if rnd.random() < long_share:
            steps = rnd.randint(18, 30)
        else:
            steps = max(2, min(14, round(rnd.gauss(mean_steps, 2.0))))
        runs.append(steps)
    return runs


def forecast(pilot_steps, weekly_cases, trials=2000, seed=7, cached=True):
    """Bootstrap: draw a week of cases from the pilot with replacement, many times; report percentiles."""
    rnd = random.Random(seed)
    per_run = [equivalents(run_tokens(s), cached) for s in pilot_steps]
    weeks = sorted(sum(rnd.choice(per_run) for _ in range(weekly_cases)) for _ in range(trials))
    pick = lambda q: weeks[min(trials - 1, int(q * trials))]
    return {"p10": round(pick(0.10)), "p50": round(pick(0.50)), "p90": round(pick(0.90))}


def tail_share(steps_list, top=0.10):
    """Share of all input-token equivalents spent by the most expensive `top` fraction of runs."""
    costs = sorted((equivalents(run_tokens(s)) for s in steps_list), reverse=True)
    k = max(1, int(len(costs) * top))
    return round(sum(costs[:k]) / sum(costs), 3)


def reweighted(pilot_steps, weekly_cases, long_share, long_from=18):
    """Re-estimate a week from the pilot's mean cost of short and long runs and an observed long-run share."""
    short = [equivalents(run_tokens(s)) for s in pilot_steps if s < long_from]
    long_ = [equivalents(run_tokens(s)) for s in pilot_steps if s >= long_from]
    per_run = (1 - long_share) * statistics.mean(short) + long_share * statistics.mean(long_)
    return round(weekly_cases * per_run)


def main(argv):
    pilot = synthetic_runs(60, seed=2026)
    week_one = synthetic_runs(1400, seed=99, mean_steps=7.0, long_share=0.15)
    f = forecast(pilot, weekly_cases=1400)
    actual = round(sum(equivalents(run_tokens(s)) for s in week_one))
    report = {
        "run_8_steps": run_tokens(8), "run_16_steps": run_tokens(16),
        "run_8_equivalents_cached": round(equivalents(run_tokens(8))),
        "run_8_equivalents_uncached": round(equivalents(run_tokens(8), cached=False)),
        "pilot_runs": len(pilot), "pilot_mean_steps": round(statistics.mean(pilot), 2),
        "pilot_long_runs": sum(s >= 18 for s in pilot), "pilot_top10_share": tail_share(pilot),
        "forecast_week_1400_cases": f,
        "week_one_mean_steps": round(statistics.mean(week_one), 2),
        "week_one_long_runs": sum(s >= 18 for s in week_one),
        "week_one_actual": actual,
        "week_one_inside_p10_p90": f["p10"] <= actual <= f["p90"],
        "reweighted_with_week_one_long_share": reweighted(pilot, 1400, sum(s >= 18 for s in week_one) / len(week_one)),
    }
    print(json.dumps(report, indent=1))
    return report


if __name__ == "__main__":
    main(sys.argv[1:])
