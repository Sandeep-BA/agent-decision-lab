"""Author: Sandeep Belgavi. How many filtered results survive a post-filtered nearest-neighbour search?

A synthetic catalogue of 20,000 book descriptions for the fictional Belgavi's Book Store is embedded as
16-dimensional vectors in 20 topic clusters. Each item has a shelf (the filter column). The script runs
exact search in pure Python, so the 'index' here is idealised: the candidate list is the true nearest
neighbours. Real approximate indexes (HNSW, IVFFlat) return fewer correct candidates, so these survivor
counts are an upper bound for post-filtering.

Compared strategies for "10 nearest items on one shelf":
  post-filter   take the 40 nearest candidates (pgvector's default hnsw.ef_search is 40), then filter
  overfetch     take 40 * f candidates, then filter
  iterative     keep pulling batches of 40 candidates until 10 match or 20,000 tuples are visited
  pre-filter    exact search over the matching rows only (the ground truth)
No database, model or network is used.
"""
import json
import math
import random

DIM, ITEMS, TOPICS, K, CANDIDATES = 16, 20_000, 20, 10, 40


def build(seed: int = 7):
    rnd = random.Random(seed)
    centers = [[rnd.gauss(0, 1) for _ in range(DIM)] for _ in range(TOPICS)]
    items = []
    for i in range(ITEMS):
        topic = i % TOPICS
        vec = [c + rnd.gauss(0, 0.35) for c in centers[topic]]
        # promo and rare are independent of topic; topic filters are clustered by construction.
        items.append({"id": f"BK-{i:05d}", "topic": topic, "vec": vec,
                      "rare": rnd.random() < 0.01, "promo": rnd.random() < 0.10})
    return centers, items


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


FILTERS = {
    "promo (10%, independent of topic)": lambda it: it["promo"],
    "rare (1%, independent of topic)": lambda it: it["rare"],
    "topic 3 (5%, a different topic than the query)": lambda it: it["topic"] == 3,
}


def ranked(items, query):
    return sorted(items, key=lambda it: dist(it["vec"], query))


def strategies(order, pred):
    truth = [it["id"] for it in order if pred(it)][:K]
    out = {"matching_rows": sum(1 for it in order if pred(it))}
    post = [it["id"] for it in order[:CANDIDATES] if pred(it)][:K]
    out["post_filter_returned"] = len(post)
    for f in (4, 10, 40):
        got = [it["id"] for it in order[:CANDIDATES * f] if pred(it)][:K]
        out[f"overfetch_x{f}_returned"] = len(got)
        out[f"overfetch_x{f}_recall"] = round(len(set(got) & set(truth)) / K, 2)
    visited, got = 0, []
    while len(got) < K and visited < ITEMS:
        batch = order[visited:visited + CANDIDATES]
        visited += len(batch)
        got += [it["id"] for it in batch if pred(it)]
    out["iterative_visited"] = visited
    out["iterative_returned"] = min(K, len(got))
    out["prefilter_returned"] = len(truth)
    return out


def main():
    centers, items = build()
    query = [c + 0.1 for c in centers[0]]
    order = ranked(items, query)
    far = max(range(1, TOPICS), key=lambda t: dist(centers[t], query))
    filters = dict(FILTERS)
    filters[f"topic {far} (5%, the farthest topic from the query)"] = lambda it: it["topic"] == far
    res = {name: strategies(order, pred) for name, pred in filters.items()}
    print(json.dumps(res, indent=2))
    return res


if __name__ == "__main__":
    main()
