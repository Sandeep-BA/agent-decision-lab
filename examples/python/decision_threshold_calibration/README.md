# Decisions-style probabilities to actions: calibration and an approve/review/deny band

**Author: Sandeep Belgavi**

A runnable companion to *From Probabilities to Actions With the Decisions API: Predicate Thresholds, Choice
Versus Score, Batched Questions and Calibration* (aicassindra.com, LLM). The OpenAI Decisions API returns a
probability for a predicate question, a value with per-value probabilities for a choice question, and a
probability per level plus a weighted score for a score question; any question can come back as a refusal.
This example shows the deterministic code that sits after such a response: a reliability check against
labelled examples, a cost-based band that approves, denies or sends an item to a person, a severity threshold
computed from level probabilities, and refusal routing.

**No provider is called.** The labelled sample is synthetic, generated from a fixed seed by `make_fixture()`.
`fixtures/decision_shaped.json` was written by hand in the documented response shape; it is not a recorded
API response.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Sample input

- `make_fixture()` builds 200 items. Each has a true chance `q` of being a real duplicate charge; the label is
  drawn with that chance, and the simulated model reports `sigmoid(2 * logit(q))`, an overconfident probability.
- `fixtures/decision_shaped.json` holds one predicate, one choice, one score and one refusal answer.

## Commands

```
python calibrate.py                                    # reliability table, bands, holdout, actions
python -m unittest discover -s . -p "test_*.py"        # run the tests
```

## Expected output

With costs of 40 for a wrong approval, 25 for a wrong denial and 3 for a human review:

- 200 items, 98 true. The top bin predicts 0.962 on average but only 0.894 are true; the bottom bin predicts
  0.039 and 0.093 are true. The simulated model is overconfident at both ends.
- A single cut at 0.5 makes 20 wrong approvals and 13 wrong denials, cost 1,125.
- The cheapest band on all 200 items denies at or below 0.10 and approves at or above 0.90: 5 wrong approvals,
  2 wrong denials, 54 reviews, cost 412.
- Fitted on items 1-100 only, the cheapest band never auto-approves (high 1.0) and denies at or below 0.05. On
  items 101-200 it costs 244 against 720 for the 0.5 cut. With 100 labels there is not enough evidence to
  trust any automatic approval.
- The fixture score answer has score 1.6, which rounds to level 2, but the probability of level 2 or higher is
  0.6; the example pages on that probability, not on the rounded score.

## Limitations

The fixture is synthetic and the band search is a grid on one small sample, so the chosen thresholds overfit;
re-fit on fresh labels whenever the model, the question instructions or the input mix change. The costs are
illustrative. The response shape follows the API reference read on 2026-10-26; check it again before use.
