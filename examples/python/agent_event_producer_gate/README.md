# Agent event producer gate

**Author: Sandeep Belgavi**

A runnable companion to *Agent Output Into an Existing Event Schema: Producer-Side Validation, Registry
Compatibility, Versioned Structured Output and Quarantine* (aicassindra.com, System design). A support agent
proposes the data of an `OrderAdjusted` event. Before anything reaches the topic, a producer gate validates the
proposal against the full registered schema and against the order being handled, the CloudEvents envelope is
built in code, and rejected proposals go to a quarantine list instead of a retry loop. The example also derives
the structured-output schema from the registered one and lists the keywords the gate must re-check because a
provider may not enforce them.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install.
- No model, broker or schema registry is contacted. `.env.example` documents that nothing is read from the environment.

## Sample input

`fixtures/proposals.json`: order 7731 (total 120.00 EUR) and four proposals: a valid 15.00 EUR
`late_delivery` adjustment, a 150.00 adjustment above the order total, a USD adjustment, and one that names
order 7713 (a transposed id). Amounts are decimal strings, which the registered schema requires.

## Commands

```
python producer.py                                     # gate the four proposals
python -m unittest discover -s . -p "test_*.py"        # run the tests
```

## Expected output

`python producer.py` publishes one event and quarantines three, naming the rule each one broke, and reports
that `amount.pattern`, `note.maxLength` and `order_id.pattern` are re-checked by the gate. The tests assert the
four outcomes, the rule named in each rejection, that schema violations (unknown field, value outside the enum,
malformed amount) are caught first, the envelope attributes, the derived schema, and that the gate runs exactly
once per proposal.

## Limitations

The schema validator implements only the keywords this schema uses; use a full JSON Schema validator in
production. Which keywords a provider enforces in structured-output mode differs by provider and changes over
time; `NOT_ENFORCED_BY_PROVIDER` is a configuration you must check against the provider's current
documentation. No registry compatibility check runs here; that belongs in CI against your registry.
