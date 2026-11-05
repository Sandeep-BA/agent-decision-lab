# Business rules in a versioned decision table, with gap and overlap checks

**Author: Sandeep Belgavi**

A runnable companion to *Keep Business Rules in a Decision Table the Agent Calls, Not in the Prompt*
(aicassindra.com, System design). The returns policy of the fictional Belgavi's Book Store is a table of rules
with a FIRST hit policy and effective-dated versions. The agent would gather the facts; `evaluate` returns the
outcome with the matched rule, its policy text and the version in force on the delivery date.

**No model is called.** The evaluator, the checks and the fixtures are deterministic.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/decision_table_policy/policy.py examples/python/decision_table_policy/fixtures/cases.json
python -m unittest discover -s examples/python/decision_table_policy -p "test_*.py"
```

## Expected output

`expected_output.json` holds the full output. In short:

| Case | Outcome | Rule | Version |
| --- | --- | --- | --- |
| Geetha: damaged sale item, day 40 | refund | R-1 | v7 |
| Jenya: member, unused book, day 44 | refund | R-3 | v7 |
| Dinky: sale item, day 12 | store credit | R-2 | v7 |
| Hansini: standard return, day 31 | refuse | R-5 | v7 |
| Tanishka: member, delivered under v6, day 40 | refuse | R-5 | v6 |
| Delivered before any version | escalate | none | none |

Checks on v7, over every combination of the three boolean inputs and the boundary days: 0 gaps; overlaps only
between the catch-all R-5 and each of R-1 to R-4, which FIRST resolves for the earlier row; no unreachable rows.
Without R-5 there are 22 gap inputs, including a damaged item on day 91. Moving the catch-all to the top makes
R-1 to R-4 unreachable. Six boundary inputs change outcome from v6 to v7, all decided by R-2 or R-3.

## Limitations

The table has three boolean inputs and one day bound per rule, so the boundary enumeration is exhaustive for it;
tables with continuous inputs on several dimensions need a solver or interval analysis instead. Only FIRST and
UNIQUE hit policies are implemented, not the full set in the DMN specification, and there is no FEEL expression
language. The policy and cases are invented for the example.
