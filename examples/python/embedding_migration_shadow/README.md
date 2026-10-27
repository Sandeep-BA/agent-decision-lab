# Embedding-model migration: overlap at k, recall at k, rank fusion and backfill gaps

**Author: Sandeep Belgavi**

A runnable companion to *Changing Embedding Models Without Breaking Search: Dual Indexes, Backfill Ordering,
Shadow Queries and Overlap at k* (aicassindra.com, Large language models). Twelve synthetic help-desk chunks
are indexed by an "old" and a "new" toy embedding model, five labelled queries run against both, and the
script reports overlap at k between the two result lists and recall at k against the labels.

**No embedding service is called.** The two models hash words into buckets with different seeds and
dimensions (64 and 96), so their vector spaces are unrelated, which is the property the guide depends on.
The new model also maps a few synonyms (refund, reimburse, money-back; parcel, package) to one token, so
it should retrieve more relevant chunks.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Sample input

`fixtures/corpus.json` (twelve chunks with a last-modified date) and `fixtures/queries.json` (five queries
with the chunk IDs judged relevant).

## Commands

```
python examples/python/embedding_migration_shadow/shadow.py 3
python -m unittest discover -s examples/python/embedding_migration_shadow -p "test_*.py"
```

## Expected output (k = 3)

Mean overlap at 3 is 0.333 for every query, while mean recall at 3 rises from 0.167 with the old model to
0.7 with the new one. Low overlap here is an improvement, which is why the guide gates cutover on judged
recall and uses overlap only to choose queries for review. The tests also check that an index refuses a
query embedded by the other model, that reciprocal rank fusion orders the guide's example as c2, c7, c11,
and that a snapshot backfill taken before 27 October misses chunks c10, c11 and c12.

## Limitations

Toy hashed vectors are not semantic embeddings, twelve chunks and five queries are far too few for a real
decision, and recall here is computed against labels written for the example.
