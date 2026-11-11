"""Dot product, cosine and L2 on the same vectors, and what mean-pooling does to vector length.
Author: Sandeep Belgavi. Standard library only; vectors are tiny synthetic fixtures.
"""
import math


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(dot(a, a))


def cosine(a, b):
    return dot(a, b) / (norm(a) * norm(b))


def l2(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def unit(a):
    n = norm(a)
    return [x / n for x in a]


def mean(vectors):
    return [sum(c) / len(vectors) for c in zip(*vectors)]


def rank(query, docs, metric):
    """Best first. Dot and cosine are similarities; L2 is a distance."""
    score = {'dot': lambda v: -dot(query, v), 'cosine': lambda v: -cosine(query, v), 'l2': lambda v: l2(query, v)}[metric]
    return [name for name, _ in sorted(docs.items(), key=lambda kv: (score(kv[1]), kv[0]))]


QUERY = [1.0, 0.0, 0.0]          # "damaged book return"
# Two help articles. RETURNS points almost the same way as the query; GIFT points elsewhere
# but is three times longer, as a weighted or unnormalised vector can be.
DOCS = {
    'returns-policy': [0.96, 0.28, 0.0],
    'gift-cards': [2.1, 2.1, 0.9],
}

# Mean-pooled document vectors built from unit-length chunk vectors.
FOCUSED_CHUNKS = [unit([1.0, 0.1, 0.0]), unit([0.9, 0.2, 0.0])]           # every chunk on topic
MIXED_CHUNKS = [unit([1.0, 0.0, 0.0]), unit([0.0, 1.0, 0.0]), unit([0.0, 0.0, 1.0])]  # one chunk on topic

if __name__ == '__main__':
    for m in ('dot', 'cosine', 'l2'):
        print(m, rank(QUERY, DOCS, m))
    for name, v in DOCS.items():
        print(name, 'dot', round(dot(QUERY, v), 3), 'cosine', round(cosine(QUERY, v), 3), 'norm', round(norm(v), 3))
    print('mean of focused chunks: norm', round(norm(mean(FOCUSED_CHUNKS)), 3))
    print('mean of mixed chunks: norm', round(norm(mean(MIXED_CHUNKS)), 3))
