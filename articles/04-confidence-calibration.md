# Probability, confidence and correctness are different measurements

Author: Sandeep Belgavi · Reviewed 18 October 2026

A decision response can contain a selected option, a probability distribution and a confidence value. Those fields answer different questions. The selected option describes the proposed branch. The distribution describes uncertainty among alternatives. Neither field proves that the supplied evidence is true or that the selected branch is correct.

<!-- diagram:Labeled cases|Predicted distributions|Calibration analysis|Held-out thresholds|Review routing -->

## Understand the provider's definition

TypeSafe documents how its confidence values are derived from answer probabilities. Read the [confidence documentation](https://docs.typesafe.ai/confidence) for the exact primitive and version. Do not treat confidence as a second independent witness that verifies the model's answer. When a confidence value is calculated from the same distribution, both numbers share the same underlying evidence.

Changing the option set can change the interpretation. A three-way route with one dominant option is not directly comparable to a binary safety question. Score confidence also has a different meaning from the expected score itself. A middle score might reflect concentrated support for the middle level or disagreement between distant levels; retaining the distribution helps distinguish those cases.

## A worked review threshold

Suppose a queue router sees 1,000 held-out tickets. You choose a threshold using a separate development set, then evaluate the frozen threshold on the held-out tickets. Record how many are automatically routed, how many go to review, and how many automatic routes are wrong. The denominator for automatic-route error is the automatically routed subset, not all tickets.

If 700 tickets are automatically routed and 14 are wrong, the observed error rate for that subset is 2 percent. That is not a guarantee for the next 700 tickets, and it says nothing about the business cost of those errors. Inspect class imbalance, rare queues and confidence intervals before deciding whether the result meets a service objective.

The 0.85 threshold in Agent Decision Lab is a teaching constant. It has not been selected from customer data, and the fixed offline fixture probabilities are not evidence of calibration. Changing the constant can demonstrate branch behavior; it cannot establish a safe production threshold.

## Measure calibration independently

Calibration asks whether predictions assigned similar probabilities have corresponding empirical frequencies. Reliability diagrams, Brier score and log loss illuminate different aspects. Accuracy alone cannot distinguish a cautiously correct model from an overconfident one. Conversely, a well-calibrated but uninformative predictor may still be operationally unhelpful.

The primary paper [On Calibration of Modern Neural Networks](https://arxiv.org/abs/1706.04599) explains why predictive accuracy and calibrated confidence should not be conflated. Its results are not a Jev benchmark. Use the measurement concepts while evaluating the actual model and workload you plan to deploy.

## Test perturbations and drift

Repeat evaluation with reordered options, paraphrased questions, conflicting evidence and irrelevant details. Keep semantically equivalent cases grouped when splitting data so near-duplicates do not leak between development and test sets. Investigate changes in both selected options and probabilities; a stable label can conceal a substantial shift in uncertainty.

A recent [Jev bias study](https://arxiv.org/abs/2610.19619) reports sensitivity under its tested formulations. That is evidence for including robustness tests, not a universal estimate of your application's error rate. Treat its findings as workload-specific and review the experimental design before generalizing.

## Make uncertainty useful to operators

A review queue should show the bounded question, permitted alternatives, relevant evidence and the reason automatic handling stopped. Avoid presenting a percentage as an objective truth about a person or transaction. Give reviewers a way to correct labels, record missing evidence and identify a broken rubric.

Version thresholds with the model, prompt, option set and dataset. When any of those changes, replay the evaluation before increasing automation. The acceptance condition is measured decision quality at an acceptable review load, not simply a high average confidence number.
