# Selective Filters Starve Post-Filtered Vector Search: Overfetch, Pre-Filter or Iterate

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/ai/vector_search_selective_filter_recall.html.

It builds 20,000 synthetic 16-dimensional book vectors in 20 topic clusters for the fictional Belgavi's Book Store and asks for the 10 nearest items that satisfy a filter, comparing a 40-candidate post-filter (pgvector's default `hnsw.ef_search`), 4x/10x/40x overfetch, an iterative scan in batches of 40 up to 20,000 visits, and an exact pre-filter. Filters are independent of content (10 percent, 1 percent) or clustered by topic (5 percent).

Prerequisites: CPython 3.11 or newer (tested with 3.13.5). No third-party dependencies (`requirements.txt` is intentionally empty). `.env.example` documents that nothing is read from the environment.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json` (asserted by the tests).

Limitations: search is exact, so the candidate list is the true nearest neighbours; a real HNSW or IVFFlat index returns fewer correct candidates, and these survivor counts are an upper bound. No database, model or network is involved. Views are my own and do not represent any employer, past or present.
