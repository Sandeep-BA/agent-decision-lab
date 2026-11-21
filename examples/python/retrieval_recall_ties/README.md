# Recall@k with ties at the k-th distance

**Author: Sandeep Belgavi**

A runnable companion to *Measure Retrieval Recall Without Penalizing Equally Near Boundary Ties* (aicassindra.com). Compares ID recall, the ANN-Benchmarks style distance-threshold recall (`d <= d_k + epsilon`) and a tie-aware recall that accepts boundary ties but requires every strictly closer item and distinct IDs.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13.5 on Windows). Standard library only.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Seven synthetic help articles with precomputed distances in `DIST`; three are tied at 0.30, the k=3 boundary.

## Commands

From this directory:

```
python recall_ties.py
python -m unittest -v
```

## Expected output

k=3, d_k=0.30. Other boundary tie: ID 0.667, threshold 1.0, tie-aware 1.0. Misses a strictly closer item: 0.333 / 1.0 / 0.667. Duplicate ID: 0.667 / 1.0 / 0.667. One wrong item: 0.667 for all three. 4 tests pass.

## Limitations

One query with exact distances supplied. Real evaluation averages over many queries and must compute ground-truth distances with the same metric and precision as the index.

Views are my own and do not represent any employer, past or present.
