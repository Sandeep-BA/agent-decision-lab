# Dot product, cosine and L2 on unnormalized vectors

**Author: Sandeep Belgavi**

A runnable companion to *Dot Product, Cosine and Unnormalized Embeddings: When the Index Metric Reorders Results* (aicassindra.com). Ranks two synthetic help articles for one query under each metric, then shows how mean-pooling unit-length chunk vectors shrinks the vector of a document that covers several topics.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

Three-dimensional vectors in `metrics.py`, chosen by hand to make the effect visible.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Five tests pass. Dot product ranks the longer gift-card vector first (2.1 against 0.96); cosine and L2 rank the returns article first; after normalising, all three agree. A mean of three orthogonal unit chunks has length 0.577.

## Limitations

Toy vectors, not a retrieval benchmark. Real embeddings have hundreds of dimensions and an approximate index adds its own recall error.

Views are my own and do not represent any employer, past or present.
