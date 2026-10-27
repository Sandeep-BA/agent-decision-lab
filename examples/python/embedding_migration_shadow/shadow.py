"""Shadow evaluation for an embedding-model migration: overlap at k, recall at k, rank fusion and gap checks.

Author: Sandeep Belgavi. Companion to "Changing Embedding Models Without Breaking Search: Dual Indexes,
Backfill Ordering, Shadow Queries and Overlap at k" (aicassindra.com, Large language models).

No embedding service is called. Two toy "models" turn text into vectors by hashing words into buckets
with different seeds and dimensions, so their vector spaces are unrelated, which is the property that
matters here. The corpus and labelled queries are synthetic help-desk snippets in fixtures/.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def embed(text, model):
    """Hashed bag of words. model = (name, dims, seed, synonyms) where synonyms maps words to a shared token."""
    name, dims, seed, synonyms = model
    vec = [0.0] * dims
    for word in text.lower().replace(",", " ").replace(".", " ").split():
        word = synonyms.get(word, word)
        h = int(hashlib.sha256(f"{seed}:{word}".encode()).hexdigest(), 16)
        vec[h % dims] += 1.0 if (h >> 8) % 2 else -1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


OLD = ("old-model", 64, "a", {})
# The new model also knows that a few words mean the same thing, so it should find more relevant chunks.
NEW = ("new-model", 96, "b", {"refund": "money-back", "reimburse": "money-back", "parcel": "package", "package": "package"})


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


class Index:
    def __init__(self, model):
        self.model, self.vectors = model, {}

    def add(self, doc_id, text):
        self.vectors[doc_id] = embed(text, self.model)

    def search(self, query_vec, k=3, query_model=None):
        if query_model is not None and query_model[0] != self.model[0]:
            raise ValueError(f"query embedded with {query_model[0]} cannot search an index of {self.model[0]}")
        scored = sorted(self.vectors, key=lambda d: (-cosine(query_vec, self.vectors[d]), d))
        return scored[:k]


def overlap_at_k(a, b, k):
    return len(set(a[:k]) & set(b[:k])) / k


def recall_at_k(ranked, relevant, k):
    return len(set(ranked[:k]) & set(relevant)) / len(relevant) if relevant else 0.0


def rrf(*rankings, k=60):
    score = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            score[doc] = score.get(doc, 0.0) + 1.0 / (k + rank)
    return sorted(score, key=lambda d: (-score[d], d))


def gap_by_bucket(old_index_ids, new_index_ids, modified):
    """Chunks present in the old index but missing from the new one, grouped by last-modified day."""
    missing = sorted(set(old_index_ids) - set(new_index_ids))
    out = {}
    for doc in missing:
        out.setdefault(modified[doc], []).append(doc)
    return out


def evaluate(k=3):
    corpus = json.loads((HERE / "fixtures" / "corpus.json").read_text(encoding="utf-8"))
    queries = json.loads((HERE / "fixtures" / "queries.json").read_text(encoding="utf-8"))
    old_idx, new_idx = Index(OLD), Index(NEW)
    for doc in corpus:
        old_idx.add(doc["id"], doc["text"])
        new_idx.add(doc["id"], doc["text"])
    rows = []
    for q in queries:
        old_r = old_idx.search(embed(q["text"], OLD), k, OLD)
        new_r = new_idx.search(embed(q["text"], NEW), k, NEW)
        rows.append({"query": q["id"], "overlap": round(overlap_at_k(old_r, new_r, k), 3),
                     "recall_old": round(recall_at_k(old_r, q["relevant"], k), 3),
                     "recall_new": round(recall_at_k(new_r, q["relevant"], k), 3)})
    mean = lambda key: round(sum(r[key] for r in rows) / len(rows), 3)
    return {"k": k, "queries": rows, "mean_overlap": mean("overlap"),
            "mean_recall_old": mean("recall_old"), "mean_recall_new": mean("recall_new")}


if __name__ == "__main__":
    print(json.dumps(evaluate(int(sys.argv[1]) if len(sys.argv) > 1 else 3), indent=1))
