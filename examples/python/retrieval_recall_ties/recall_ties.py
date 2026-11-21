"""Recall@k when the k-th nearest distance is tied. Author: Sandeep Belgavi.

Synthetic catalogue: help-desk articles at the fictional Belgavi's Book Store,
with exact distances from one query already computed. Three recall rules:

- id_recall: |returned ∩ exact top-k IDs| / k. Penalises a correct but
  differently ordered tie at the boundary.
- threshold_recall: the ANN-Benchmarks style count of returned items whose
  distance is <= d_k + epsilon, divided by k. Accepts ties, but also accepts
  duplicates and can miss a strictly closer item.
- tie_aware_recall: distinct returned items within d_k + epsilon, capped by
  how many strictly closer items were included. 1.0 only when every item
  strictly closer than d_k is present and the rest are boundary ties.
"""

DIST = {
    'KB-101 returns window': 0.10,
    'KB-102 refund to card': 0.20,
    'KB-103 damaged book': 0.30,
    'KB-104 wrong edition': 0.30,
    'KB-105 late delivery refund': 0.30,
    'KB-106 gift card refund': 0.45,
    'KB-107 store pickup': 0.60,
}


def exact_topk(dist, k):
    """Sorted by distance, then by ID: the tie-break is arbitrary but fixed."""
    return [i for i, _ in sorted(dist.items(), key=lambda x: (x[1], x[0]))[:k]]


def kth_distance(dist, k):
    return sorted(dist.values())[k - 1]


def id_recall(returned, dist, k):
    return len(set(returned[:k]) & set(exact_topk(dist, k))) / k


def threshold_recall(returned, dist, k, epsilon=1e-3):
    t = kth_distance(dist, k) + epsilon
    return sum(1 for i in returned[:k] if dist[i] <= t) / k


def tie_aware_recall(returned, dist, k, epsilon=1e-3):
    dk = kth_distance(dist, k)
    distinct = list(dict.fromkeys(returned[:k]))
    within = [i for i in distinct if dist[i] <= dk + epsilon]
    closer = {i for i, d in dist.items() if d < dk - epsilon}
    missing_closer = closer - set(distinct)
    good = min(len(within), k - len(missing_closer))
    return good / k


def report(name, returned, k=3):
    return (name, round(id_recall(returned, DIST, k), 3), round(threshold_recall(returned, DIST, k), 3),
            round(tie_aware_recall(returned, DIST, k), 3))


CASES = [
    ('exact order', ['KB-101 returns window', 'KB-102 refund to card', 'KB-103 damaged book']),
    ('other boundary tie', ['KB-101 returns window', 'KB-102 refund to card', 'KB-105 late delivery refund']),
    ('misses a closer item', ['KB-101 returns window', 'KB-104 wrong edition', 'KB-105 late delivery refund']),
    ('duplicate', ['KB-101 returns window', 'KB-102 refund to card', 'KB-102 refund to card']),
    ('one wrong item', ['KB-101 returns window', 'KB-102 refund to card', 'KB-106 gift card refund']),
]


def main():
    print('k=3, d_k =', kth_distance(DIST, 3), 'exact top-3 =', exact_topk(DIST, 3))
    print('case | id_recall | threshold_recall | tie_aware_recall')
    for name, returned in CASES:
        print(' | '.join(str(x) for x in report(name, returned)))


if __name__ == '__main__':
    main()
