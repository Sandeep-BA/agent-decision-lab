# Overlapping Chunks Fill Top-k With the Same Passage: Merge by Source Span First

Author: **Sandeep Belgavi**.

Original teaching example for https://aicassindra.com/blogs/ai/retrieval_overlapping_chunks_span_merge.html.

`example.py` splits four synthetic Belgavi's Book Store help articles into 360-character windows with 120 characters of overlap, ranks them with a deterministic lexical scorer that stands in for a retriever, and compares a plain top-6 context with one built by merging hits from the same document whose character spans overlap, filled to the same character budget.

Prerequisites: CPython 3.11 or newer (recorded with 3.13.5 on Windows 11). Standard library only; `requirements.txt` is intentionally empty and `.env.example` documents that nothing is read from the environment. No network, no credentials and no model call.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json` (plain top-6: 24.6 percent of the context is repeated text and only two documents appear; span-merged: no repeated text and a third document fits in the same budget).

Limitations: the scorer is lexical and the corpus tiny, so the numbers show the mechanism, not retrieval quality. Measure the repeated share on your own index and chunker. Views are my own and do not represent any employer, past or present.
