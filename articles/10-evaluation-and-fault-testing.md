# Evaluate the decision model and the application as separate systems

Author: Sandeep Belgavi · Reviewed 18 October 2026

A thousand passing tests can establish useful software properties without establishing model intelligence. Conversely, a strong benchmark score can coexist with a broken authorization check. Evaluate the probabilistic component and the surrounding application separately, then test the complete workflow where their failures interact.

<!-- diagram:Contract fixtures|Model evaluation set|Robustness variants|End-to-end scenarios|Release evidence -->

## What the repository tests establish

Agent Decision Lab runs ten boundary scenarios for each of 100 recipes. The cases cover valid recommendations, wrong scope, exhausted budget, missing evidence, absent approval, review, block, invalid output, provider failure and uncertainty. A separate provider-contract test checks request construction and response parsing.

Those tests use controlled responses. They can prove that an invalid option is rejected in the tested path or that a model is not called after a scope failure. They cannot prove that Jev identifies fraud, that a local model understands a document, or that a prompt resists every injection. The fixture provider returns fixed probabilities and is explicitly named `fixture-no-inference` in output.

## Build a model evaluation set

For each intended use case, collect authorized examples with the state available at decision time. Label outcomes using a written rubric and record disagreements. Exclude later information that the real system would not have had. Otherwise, an impressive offline score may depend on accidental access to the answer.

Split examples by source, customer, incident or time as appropriate. Near-duplicate tickets or repeated versions of a document should not be scattered across training and test splits. Keep a final held-out set untouched while tuning prompts and thresholds.

For categorical decisions, report a confusion matrix and per-class measures. For probability quality, include Brier score or log loss and calibration analysis. For automation, report error among automatically handled cases and the fraction sent to review. Use confidence intervals where the sample supports them and state when rare cases are too few for a reliable estimate.

## Add robustness variants

Reorder options, paraphrase instructions without changing meaning, add irrelevant material, remove critical evidence and introduce contradictory sources. Keep variants linked to their original case so evaluation does not pretend they are independent samples. Measure changes in probability distributions as well as labels.

The [Jev bias study](https://arxiv.org/abs/2610.19619) motivates checking formulation and ordering effects, but its results are not a substitute for your workload. The [calibration literature](https://arxiv.org/abs/1706.04599) likewise supplies methods rather than a deployment approval.

## Exercise infrastructure failures

Simulate a provider timeout, malformed JSON, unknown model identifier, oversized body and rate-limit response. Test cancellation while a request is outstanding. Confirm that error messages do not expose credentials or raw sensitive evidence. Verify that an uncompleted model call does not produce a success event in the audit trail.

For a workflow with real effects, add duplicate delivery, revoked approval, stale state and uncertain external outcomes. These require a durable ledger and reconciliation behavior beyond the current recommendation-only Java runtime. A mock success response is insufficient evidence for a payment or deployment integration.

## Publish a useful release report

Separate four categories: unit fixtures, real protocol or HTTP transport checks, live provider smoke tests, and task-quality evaluation. Record versions, commands, dataset provenance and known gaps. Do not combine them into a single “tests passed” badge that suggests more than was measured.

The acceptance decision should identify which failures block release and who owns them. A model update might require new thresholds; an HTTP client update might require transport regression tests; an authorization change needs denial tests before any model runs. This distinction keeps evaluation focused and makes public claims easier to verify.
