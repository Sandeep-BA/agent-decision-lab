"""Project token volume after a model switch from per-kind ratios. Standard library only.

Author: Sandeep Belgavi.
"""
from collections import defaultdict


def ratios(samples, count_old, count_new):
    """samples: (kind, text) pairs from real traffic. Returns new/old ratio per kind."""
    old, new = defaultdict(int), defaultdict(int)
    for kind, text in samples:
        old[kind] += count_old(text)
        new[kind] += count_new(text)
    return {k: new[k] / old[k] for k in old if old[k]}


def projected_tokens(monthly_tokens_by_kind, kind_ratios):
    return sum(t * kind_ratios.get(k, 1.0) for k, t in monthly_tokens_by_kind.items())


# Measured on 2026-10-29 (o200k_base -> Qwen2.5), see README.
MEASURED = {'english': (93, 98), 'json_indented': (216, 246), 'hindi': (47, 138), 'kannada': (49, 195), 'logs': (517, 661)}


def article_mix():
    r = {k: new / old for k, (old, new) in MEASURED.items()}
    mix = {'english': 0.6, 'json_indented': 0.3, 'hindi': 0.1}
    return projected_tokens(mix, r)


if __name__ == '__main__':
    print('projected token factor for the article mix: %.3f' % article_mix())
