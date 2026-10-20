# Online evaluation: traffic mix shift versus quality drop

**Author: Sandeep Belgavi**

A runnable model of the weekly report in *Online Evaluation of a Production Agent: Stratified
Sampling, a Judge Budget and Telling a Traffic-Mix Shift From a Real Quality Drop*
(aicassindra.com, agents). It generates a synthetic week of finished agent runs in three
segments, draws a stratified judged sample with a fixed seed, and reports per-segment pass rates
with 95% Wilson intervals, the aggregate, the aggregate reweighted to a reference mix, and the
split of the true change into a mix effect and a rate effect.

## Prerequisites

- Python 3.11 or newer. Standard library only (`random`, `math`, `json`, `argparse`,
  `unittest`); nothing to install.
- No network, no model provider, no credentials. The "judge" label is part of the synthetic
  fixture; no model scores anything. `.env.example` documents that nothing is read from the
  environment.

## Sample input

`fixtures/scenarios.json` defines the reference week (mix 50/30/20, pass rates 0.92/0.85/0.70)
and three weeks: `unchanged`, `mix-shift` (30/30/40, same rates) and `hidden-regression`
(70/20/10, technical drops to 0.55). Each week is expanded into 20,000 runs with a fixed seed.

## Commands

From the repository root:

```sh
python examples/python/online_eval_mix_shift/online_eval.py --week hidden-regression --allocation uniform
python examples/python/online_eval_mix_shift/online_eval.py --week hidden-regression --allocation equal
python examples/python/online_eval_mix_shift/online_eval.py --week mix-shift --allocation equal
python examples/python/online_eval_mix_shift/online_eval.py --week unchanged --allocation neyman
python -m unittest discover -s examples/python/online_eval_mix_shift -p "test_*.py"
```

Options: `--budget` (judged runs, default 600) and `--seed` (default 20261020).

## Expected output (default seed; verified with Python 3.13)

```
week=hidden-regression allocation=uniform budget=600 runs=20000
  billing   share=0.702 judged=421 passed=381 rate=0.905 interval=[0.873, 0.929] baseline=0.92 alert=False
  account   share=0.202 judged=121 passed=107 rate=0.884 interval=[0.815, 0.930] baseline=0.85 alert=False
  technical share=0.096 judged= 58 passed= 32 rate=0.552 interval=[0.425, 0.673] baseline=0.70 alert=True
aggregate=0.867 (reference 0.855) aggregate_alert=False reweighted=0.828
true change split: mix_effect=+2.9 rate_effect=-1.5 points
```

The aggregate rises while the technical segment got worse; only the per-segment rule and the
reweighted figure show it. With `--allocation equal` the technical segment gets 200 judged runs
and a much narrower interval. In the `mix-shift` week the aggregate falls by nearly seven points in
this sample and the aggregate rule fires, while no segment alert fires and the reweighted figure
stays near the reference.

The `unchanged --allocation neyman` run is worth reading too: with this seed the aggregate sample
comes out at 0.826 and the aggregate rule fires although nothing changed. That is sampling noise
on 600 judged runs, and it is why an aggregate threshold must account for the aggregate's own
uncertainty, not only a fixed number of points.

## Tests

`test_online_eval.py` (7 tests) checks the Wilson intervals and the mix/rate decomposition quoted
in the guide, the three allocation rules, and over many seeds that equal allocation catches the
hidden regression, is at least as sensitive as uniform allocation, and that a pure mix shift fires
the aggregate rule while segment rules mostly stay quiet.

## Limitations

- Three segments with known true rates; real segments are fuzzier and their true rates unknown.
- The baseline is treated as exact. A real baseline has its own interval and deserves a
  two-sample test.
- The judge label is perfect. A real judge has errors that can differ by segment; measure its
  agreement with reviewers per segment.
- Output values depend on Python's `random` module for a given seed; the tests assert
  properties over many seeds rather than exact samples.
