# Compile derived metric formulas before scoring

**Author: Sandeep Belgavi**

A runnable companion to *promptfoo 0.126.0 Rejects Unsupported Derived Metric Formulas Before Any Test Runs* (aicassindra.com). An original Python model of the grammar promptfoo 0.126.0 documents for string derived-metric formulas: numeric literals, score names and __count, parentheses, + - * /, unary signs, the six comparisons without chains, condition ? a : b, and at most 1,024 characters. Formulas are compiled once before any row is scored; per-row evaluation keeps the last value and records a debug line when a score is missing. An optional known-names check catches misspelled scores before scoring.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Four synthetic score rows (tp, fp, fn) in `ROWS`.

## Commands

From this directory:

```
python formula.py
python -m unittest -v
```

## Expected output

F1 over running totals 0.75; zero rows 0.0; unguarded tp / (tp + fp) with zeros is NaN. Rejected at compile time: max(tp, fp), tp.constructor, tp = 1, 0 < tp < 1, a 1,025-character formula, tp ** 2, tp; fp. A misspelled score fnn compiles, stays 0.0 and logs 4 lines; with the known-names check it is rejected. 7 tests pass.

## Limitations

Not promptfoo code: promptfoo parses with acorn and accepts every JavaScript numeric literal form, while this tokenizer accepts decimal and exponent forms only. Use it to test your formulas' shape, then run promptfoo itself.

Views are my own and do not represent any employer, past or present.
