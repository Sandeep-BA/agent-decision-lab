# Rules first, agent for the residual

**Author: Sandeep Belgavi**

A runnable companion to *Rules First, Agent for the Residual: Adding an Agent to a Deterministic Pipeline
Without Giving Up What Already Works* (aicassindra.com, agents). An accounts-payable pipeline already
decides most invoices with deterministic rules: duplicates are rejected and invoices that match their
purchase order within 2 percent, with all goods received, are approved. The example adds an agent only for
the invoices those rules cannot decide and keeps three parts deterministic:

- the **router** sends an invoice to the agent only when no rule decided it;
- the **validator** refuses any agent action that breaks a hard constraint: no approval without a purchase
  order, no approval of goods not received, no agent approval above 5,000;
- the **acceptance policy** takes an agent decision only at or above a confidence threshold; escalations
  and everything else go to a person.

`StubAgent` stands in for a model. Its behaviour per exception type is a fixed table (`STUB_PROFILE`), so
the figures below describe the stub, not any real model. Replace it with a real client to measure your
own model on your own labelled cases.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt`).
- No environment variables or credentials (`.env.example`). Nothing calls a model provider.

## Commands

From the repository root:

```sh
python examples/python/residual_router/router.py --threshold 0.8
python examples/python/residual_router/router.py --threshold 0.6
python examples/python/residual_router/router.py --threshold 0.9
python examples/python/residual_router/router.py --threshold 0.8 --freight-rule
python -m unittest discover -s examples/python/residual_router -p "test_*.py"
```

## Expected output (verified with Python 3.13)

1,000 synthetic invoices; the rules decide 851 and none of them wrongly; 149 go to the agent.

| Command | Agent accepted | Wrong among accepted | Refused by validator | Human queue | Automated |
| --- | --- | --- | --- | --- | --- |
| `--threshold 0.8` | 105 | 0 | 20 | 44 | 95.6% |
| `--threshold 0.6` | 109 | 4 | 20 | 40 | 96.0% |
| `--threshold 0.9` | 9 | 0 | 20 | 140 | 86.0% |
| `--threshold 0.8 --freight-rule` | 94 | 0 | 21 | 42 | 95.8% (the new rule approves 4 invoices wrongly) |

The validator refusals are the stub's wrong approvals: 10 without a purchase order, 6 for goods not
received and 4 above the approval limit. `--freight-rule` promotes a pattern the agent kept approving
(invoice exceeds the order by at most 60) into a rule; the rule also matches four small orders whose
excess is a price error, which is why a promoted rule needs the same evaluation as any other change.

## Tests

`test_router.py` (7 tests): fixture determinism; the rules decide 851 invoices without error; the validator
refuses the 20 unsafe approvals whatever the confidence; the threshold trade-off at 0.6, 0.8 and 0.9;
escalations reach a person; the promoted rule's four wrong approvals; an unknown action is refused.

## Limits

The categories, amounts and the stub's error profile are invented to make the arithmetic visible. Real
exception mixes drift, confidence scores from real models are often poorly calibrated, and a real
validator needs the constraints your finance team actually enforces.
