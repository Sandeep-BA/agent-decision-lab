# A B-tree searched with a changed collation

**Author: Sandeep Belgavi**

A runnable companion to *When an OS Upgrade Changes Collation: PostgreSQL Indexes That Silently Miss Rows* (aicassindra.com). Two illustrative comparators (OLD ignores hyphens and spaces at the first level, NEW does not), a sorted list standing in for B-tree leaves, binary search, an adjacent-order check and a uniqueness check by search.

## Prerequisites

- Python 3.11 or newer. Standard library only. No PostgreSQL or glibc locale is used.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Twelve synthetic shelf codes in `SHELF`. `python collation_model.py` prints both orders, each lookup and the violations.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Six tests pass. Searching the OLD-built index with NEW misses 1-2, 1 3 and A-2; the order check reports three adjacent violations; inserting 1-2 again is accepted; rebuilding under NEW fixes all lookups.

## Limitations

The comparators are illustrations, not glibc 2.27 or 2.28 collation tables, and a sorted list is not a real B-tree. Use amcheck on a real database.

Views are my own and do not represent any employer, past or present.
