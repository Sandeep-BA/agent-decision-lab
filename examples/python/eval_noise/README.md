# Eval noise: task, generation and grader variance

**Author: Sandeep Belgavi**

A runnable companion to *Two Sources of Eval Noise* (aicassindra.com, LLM). The support team at Belgavi's Book
Store scores its returns agent with a judge. This example estimates the three variance components of an eval
score from nested repeats, `scores[task][generation][grade]`, by the method of moments, and computes the 95%
half-width of the eval mean for a given number of tasks, generations per task and grades per generation.
Synthetic data comes from known settings (task pass rates of 0.05, 0.5 and 0.95, and a judge that flips each
verdict with probability 0.1), so the estimates can be checked against the implied values.

**No model or judge is called.**

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` lists nothing to install.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/eval_noise/noise.py
python -m unittest discover -s examples/python/eval_noise -p "test_*.py"
```

## Expected output

```
estimated  task 0.080  generation 0.075  grader 0.094
implied    task 0.086  generation 0.074  grader 0.090
n=200 K=1 G=1  +/- 6.4 points
n=200 K=4 G=1  +/- 4.9 points
n=200 K=1 G=4  +/- 6.0 points
n=800 K=1 G=1  +/- 3.2 points
```

A judge that flips binary verdicts with probability f scales real task and generation variance by
(1 - 2f) squared, 0.64 here, so a noisy judge also compresses the differences you want to measure. Five
unittest cases check the printed estimates, agreement with the implied values across seeds, a perfect grader,
the shrink factor and the half-widths quoted in the article.

## Limitations

The estimator assumes independent generations and independent grades. Re-grading with the same judge, prompt
and seed can return correlated verdicts, which makes grader variance look smaller than it is. Small pilots can
give negative estimates; clip at zero and collect more data. Clustered tasks need clustered standard errors.
