# Shadow index comparison for an embedding model change

**Author: Sandeep Belgavi**

A runnable companion to *Switch Embedding Models Behind a Shadow Index and Measure Overlap First* (aicassindra.com). Two small deterministic embedders stand in for an old and a new model: hashed bag of words and hashed character trigrams, both 64 dimensions. Sixteen synthetic help articles are indexed twice. Sixteen labelled queries in two classes (clean wording and misspellings) are run against both indexes. The example reports labelled hits at 3, overlap at 3 between the two result lists, what happens when a new-model query vector is searched against old-model document vectors, and a per-class cutover plan.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

`DOCS` and `QUERIES` in `shadow.py`.

## Commands

From this directory:

```
python shadow.py
python -m unittest -v
```

## Expected output

Clean queries: old index 7 of 8 hits at 3, new index 8 of 8, mean overlap 0.42. Misspelled queries: old 4 of 8, new 7 of 8, mean overlap 0.25. Mixed vectors: 2 of 8 and 0 of 8. Plan: switch both classes. 5 tests pass.

## Limitations

Toy embedders and a 16-document corpus. The numbers show how to read the measurements, not how any real embedding model performs. Real migrations also need index build time, cost and latency measurements.

Views are my own and do not represent any employer, past or present.
