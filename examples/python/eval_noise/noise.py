"""Author: Sandeep Belgavi. Separating task, generation and grader variance in an eval score.

Companion to "Two Sources of Eval Noise" (aicassindra.com). Synthetic nested scores
scores[task][generation][grade] come from known settings, so the method-of-moments estimates can be checked
against the values those settings imply. No model or judge is called.
"""
import math
import random
from statistics import mean, variance


def components(scores):
    """scores[task][sample][grade] -> (task, generation, grader) variance estimates."""
    K, G = len(scores[0]), len(scores[0][0])
    grader = mean(variance(grades) for task in scores for grades in task)
    per_output = [[mean(grades) for grades in task] for task in scores]
    generation = mean(variance(outs) for outs in per_output) - grader / G
    task_means = [mean(outs) for outs in per_output]
    task = variance(task_means) - generation / K - grader / (K * G)
    return task, generation, grader


def synthetic(n=300, K=4, G=3, flip=0.1, seed=7, levels=(0.05, 0.5, 0.95)):
    rng = random.Random(seed)
    data = []
    for _ in range(n):
        p = rng.choice(levels)
        task = []
        for _ in range(K):
            correct = rng.random() < p
            task.append([int(correct != (rng.random() < flip)) for _ in range(G)])
        data.append(task)
    return data


def implied(flip=0.1, levels=(0.05, 0.5, 0.95)):
    """Components implied by the synthetic settings; a flipping grader scales real variance by (1 - 2 flip)^2."""
    shrink = (1 - 2 * flip) ** 2
    task = (mean(p * p for p in levels) - mean(levels) ** 2) * shrink
    generation = mean(p * (1 - p) for p in levels) * shrink
    grader = flip * (1 - flip)
    return task, generation, grader


def half_width(task, generation, grader, n, K, G, z=1.96):
    """95% half-width of the eval mean, in percentage points."""
    return 100 * z * math.sqrt((task + generation / K + grader / (K * G)) / n)


if __name__ == '__main__':
    est = components(synthetic())
    print('estimated  task %.3f  generation %.3f  grader %.3f' % est)
    print('implied    task %.3f  generation %.3f  grader %.3f' % implied())
    for n, K, G in ((200, 1, 1), (200, 4, 1), (200, 1, 4), (800, 1, 1)):
        print('n=%d K=%d G=%d  +/- %.1f points' % (n, K, G, half_width(0.10, 0.08, 0.03, n, K, G)))
