"""Detect silent truncation of embedding inputs. Author: Sandeep Belgavi.

Original example for the aicassindra.com article "Embedding Inputs Longer Than the Model Limit Are Cut Off
Without an Error". Two checks: (1) the token count reported for an input equals the applied limit, and (2) the
vector of a chunk does not change when its last sentence is removed. Standard library only.

Offline (default): runs both checks against FakeEmbedServer, which truncates at a configurable limit.
Live: python probe.py --live [--model all-minilm]  calls an Ollama server at $OLLAMA_URL (default
http://127.0.0.1:11434) and prints what it measured; nothing is sent anywhere else.
"""
import argparse
import json
import math
import os
import urllib.error
import urllib.request

HEAD = "Return policy for Belgavi's Book Store. Books may be returned within thirty days of delivery in unused condition. " * 4
FILLER = "Shipping notes: parcels leave the warehouse each weekday morning and are tracked by courier. " * 40
TAIL = "Damaged items: a book that arrives damaged can be returned for a full refund within ninety days."
QUERY = "Can I return a damaged book after two months?"


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b)) / math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))


class FakeEmbedServer:
    """Splits on whitespace, keeps the first `limit` tokens (like truncate=true) and hashes words into a vector."""

    def __init__(self, limit=256, dims=64, truncate=True):
        self.limit, self.dims, self.truncate = limit, dims, truncate

    def embed(self, text, truncate=None):
        words = text.split()
        if len(words) > self.limit and not (self.truncate if truncate is None else truncate):
            return {"http_status": 400, "error": "the input length exceeds the context length"}
        words = words[: self.limit]
        vec = [0.0] * self.dims
        for w in words:
            vec[sum(map(ord, w.lower().strip(".:,"))) % self.dims] += 1.0
        return {"embeddings": [vec], "prompt_eval_count": len(words)}


class OllamaClient:
    def __init__(self, url, model):
        self.url, self.model = url.rstrip("/"), model

    def embed(self, text, truncate=None):
        body = {"model": self.model, "input": text}
        if truncate is not None:
            body["truncate"] = truncate
        req = urllib.request.Request(self.url + "/api/embed", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except urllib.error.HTTPError as e:
            return {"http_status": e.code, "error": e.read().decode()[:200]}


def probe(client, limit):
    """Return the measurements the article reports, for any client with embed(text, truncate=None)."""
    rows = {}
    for name, text in [("head", HEAD), ("head+filler", HEAD + FILLER), ("head+filler+tail", HEAD + FILLER + TAIL), ("tail", TAIL)]:
        r = client.embed(text)
        rows[name] = {"chars": len(text), "tokens": r["prompt_eval_count"], "at_limit": r["prompt_eval_count"] >= limit}
    a = client.embed(HEAD + FILLER)["embeddings"][0]
    b = client.embed(HEAD + FILLER + TAIL)["embeddings"][0]
    q = client.embed(QUERY)["embeddings"][0]
    t = client.embed(TAIL)["embeddings"][0]
    strict = client.embed(HEAD + FILLER + TAIL, truncate=False)
    return {
        "rows": rows,
        "tail_changes_vector": round(cosine(a, b), 6) != 1.0,
        "query_vs_long_chunk": round(cosine(q, b), 4),
        "query_vs_tail_chunk": round(cosine(q, t), 4),
        "truncate_false": strict.get("error", "accepted"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="call a local Ollama server instead of the fake")
    ap.add_argument("--model", default="all-minilm")
    ap.add_argument("--limit", type=int, default=256, help="the token limit the server applies")
    a = ap.parse_args()
    client = OllamaClient(os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434"), a.model) if a.live else FakeEmbedServer(a.limit)
    print(json.dumps({"mode": "live" if a.live else "offline fake", **probe(client, a.limit)}, indent=2))


if __name__ == "__main__":
    main()
