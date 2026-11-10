# Judge model upgrade: agreement, kappa and flips on an anchor set

**Author: Sandeep Belgavi**

A runnable companion to *Upgrading the Judge Model Without Moving the Goalposts* (aicassindra.com). Exact Cohen's kappa (with fractions), pass-rate shift and directional flips between an old and a new judge, with a decision rule that says when the baseline has to be rescored.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

`fixture()` in `rebaseline.py`: twenty synthetic pass/fail labels from a person, the old judge and a more lenient new judge.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Five tests pass. For the fixture, kappa against the human labels is 5/8 for the old judge and 7/17 for the new one, the new judge flips three fails to passes and none the other way, and the decision is to reject it. A new judge identical to the human labels still requires a re-baseline because it flips 3 of 20 verdicts.

## Limitations

Twenty items are far too few to estimate kappa precisely; the thresholds are illustrative. No judge model is called and labels are synthetic.

Views are my own and do not represent any employer, past or present.
