# Tables in a retrieval corpus: three chunkings and a strict answerability check

**Author: Sandeep Belgavi**

A runnable companion to *Tables in a Retrieval Corpus* (aicassindra.com, LLM). A synthetic Belgavi's Book Store
corpus of three tables (returns, shipping, membership; 13 rows) and three paragraphs, ten questions whose answers
sit in one cell, BM25 (k1 = 1.2, b = 0.75) in pure Python, and three chunkings: fixed 160-character windows over
the markdown table, one chunk per row without headers, and one chunk per row serialized with the table title and
every header (`serialize_rows`). A chunk counts as answerable only if it contains the row name, the column header
and the cell.

**No model or embedding service is called.**

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` lists nothing to install.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

Run from the repository root.

```
python examples/python/table_row_chunks/table_chunks.py
python -m unittest discover -s examples/python/table_row_chunks -p "test_*.py"
```

## Expected output

```
fixed            chunks=12  row_and_cell@3=10/10  answerable@1=1/10  answerable@3=1/10
row              chunks=16  row_and_cell@3=10/10  answerable@1=0/10  answerable@3=0/10
row_with_header  chunks=16  row_and_cell@3=10/10  answerable@1=7/10  answerable@3=10/10
```

Four unittest cases: the numbers above, the serializer output, the strict check rejecting a header-less row, and empty cells being skipped.

## Limitations

A tiny fixture with lexical retrieval only; dense retrieval and real documents will give different rates. Three
questions lose rank 1 to short paragraphs that share common words, which a stopword list or hybrid search would
change. Aggregation questions over many rows need a query tool, not retrieval.
