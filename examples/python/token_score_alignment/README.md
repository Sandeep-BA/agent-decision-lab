# Align generated tokens with their scores

**Author: Sandeep Belgavi**

A runnable companion to *Align Generated Token Scores Before Comparing Model Output Likelihoods* (aicassindra.com). A pure-Python model of the bookkeeping around Transformers `generate(..., output_scores=True, return_dict_in_generate=True)` and `compute_transition_scores`: generated positions are the last `len(scores)` columns, finished rows keep receiving the pad token and are not masked without beam indices, and `scores` are processed (temperature-dependent) rather than raw logits.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13.5 on Windows). Standard library only. No torch, no model and no tokenizer.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Two left-padded rows, a six-token vocabulary and five steps of synthetic logits in `RAW`.

## Commands

From this directory:

```
python alignment.py
python -m unittest -v
```

## Expected output

Row 0 (stops at step 2): -3.5509 unmasked, -1.7011 masked. Row 1: -2.9797 either way. Slicing each row by its unpadded prompt length gives 6 and 5 positions instead of 5 and 5. Processed scores at temperature 0.7 give -1.6104 for row 1. Traces with different tokenizer hashes or temperatures are refused. 6 tests pass.

## Limitations

Greedy-style rows only; beam search, where `compute_transition_scores` does mask with beam indices, is not modelled. Check the behaviour of your installed Transformers version before relying on it.

Views are my own and do not represent any employer, past or present.
