# Exact paired regression gate

**Author: Sandeep Belgavi**

A runnable companion to *How Many Eval Cases Does It Take to Catch a Three-Point Drop?* (aicassindra.com). A one-sided exact conditional test over baseline-only and candidate-only passes.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no database server, no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

Loss and win counts in the tests: 15 and 5, 5 and 0, 0 and 0, 0 and 5.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Three tests pass. `degradation_pvalue(15, 5)` is 21700/1048576, about 0.0207, and `degradation_pvalue(5, 0)` is 0.03125.

## Limitations

The test assumes independent paired binary outcomes. It is not a noninferiority test and not a complete release policy. No model is evaluated.

Views are my own and do not represent any employer, past or present.
