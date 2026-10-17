# Design a typed decision contract before selecting a model

Author: Sandeep Belgavi · Reviewed 18 October 2026

When a model controls a branch in software, the branch needs a contract. The contract describes the evidence, permitted answers, uncertainty behavior and downstream consequences. It is more useful than a prompt that asks the model to be careful, because the application can validate and test the contract without knowing how the model reached its answer.

<!-- diagram:Reviewed state|Typed question|Provider response|Contract validator|Application branch -->

## Map each question to the right shape

The [TypeSafe API reference](https://docs.typesafe.ai/api) documents Choice, Score and Noul answers. Choice is appropriate for a finite set of alternatives. Score uses ordered rubric levels. Noul expresses a yes/no probability. The current documentation also includes [Box](https://docs.typesafe.ai/primitives/box) for locating something in an image; model support must be checked separately rather than assumed from the existence of the API field.

For a support router, define a Choice between technical support, account administration and review. For a document-quality check, use a Score rubric with observable descriptions, such as missing evidence, partial evidence and adequate evidence. For a specific factual condition, ask a Noul question. A single broad question such as “Is this customer safe?” mixes unclear labels, hidden policy and potentially inappropriate inferences. Decompose it into evidence checks the application actually needs.

The question identifier is an application mapping key. Put the real decision criteria in instructions and criteria, not only in an identifier such as `urgent_customer`. The provider documentation explains which fields reach inference; an expressive JSON key is not a substitute for a fully specified question.

## Keep state small and provenance visible

Imagine a reviewer deciding whether a proposed refund merits human consideration. It needs the relevant order facts, the supplied refund rule and the customer's request. It does not need the entire customer history, payment credentials or unrelated private messages. Minimize state before the provider call, not after logging the full request.

Separate trusted policy from untrusted evidence. Label the source and collection time of evidence when those facts affect the decision. If the source document contains a sentence telling the model to ignore its instructions, that sentence remains source content. The application's permission boundary must remain outside the provider response.

In the Java examples, every recipe declares two required evidence fields. The engine copies only those fields into model state and rejects missing or oversized values. This is deliberately simple: it demonstrates allowlisting but does not implement automatic PII detection, field-level encryption or legal retention policy.

## Validate meaning-bearing structure

For a Choice response, check that the option set matches the request, probabilities are finite and between zero and one, their sum is within an explicit tolerance, and the selected option is one of the maximum-probability options. Also require the returned model identifier so a trace can distinguish versions. Unknown options must fail closed rather than being mapped to the nearest familiar string.

These checks catch a malformed response, not a wrong judgment. A distribution assigning high probability to the wrong queue is structurally valid. That distinction should appear in dashboards: schema failure, provider failure, uncertain judgment and wrong judgment are different categories with different owners.

## Work through a failure path

Suppose the API returns a new option named `execute_refund` although the request allowed only `proceed`, `review` and `block`. The Java engine rejects it as `INVALID_OUTPUT`; it does not interpret the name as a tool call. If the model returns `review`, the application preserves that outcome instead of turning it into permission because the HTTP request succeeded.

Try changing the fixture distribution in `EngineTest` so it sums to 1.3 or selects a non-maximum option. The contract should reject it before approval. Then test a valid but deliberately wrong distribution: the validator will accept its shape, demonstrating why a separate labeled evaluation is required.

The [source repository](https://github.com/Sandeep-BA/agent-decision-lab) implements the Choice contract only. Its article coverage of other primitives is explanatory, not a claim that every primitive has a tested Java adapter.
