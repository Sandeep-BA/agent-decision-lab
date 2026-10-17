# Prepare decision data before considering a local-model fine-tune

Author: Sandeep Belgavi · Reviewed 18 October 2026

Fine-tuning is not the first remedy for an unclear decision contract. If reviewers disagree about what the labels mean, training can reproduce that ambiguity more efficiently. Begin with a bounded task, an evidence policy and a labeling rubric. Then compare prompting, retrieval, deterministic rules and a trained model on the same held-out cases.

<!-- diagram:Task rubric|Authorized examples|Grouped split|Baseline evaluation|Optional local training|Held-out review -->

## Distinguish provider configuration from training

The [TypeSafe model documentation](https://docs.typesafe.ai/models) describes customization through request state and question criteria rather than customer fine-tuning or LoRA adaptation of Jev. Do not advertise a “Jev fine-tuning lab” when the actual code only changes a prompt or trains a separate classifier.

A local SLM fine-tune is a different project. It requires suitable model weights, a compatible license, a training framework, hardware and an evaluation plan. The Java decision interface can host another adapter later, but a matching response shape does not establish that the new model has the same calibration or capabilities.

## Design a useful example record

For a support-routing experiment, a record might contain an identifier, the message excerpt, the allowed queues, the correct queue under the rubric, the rubric version and a source-group identifier. Add a flag for ambiguous cases rather than forcing every example to have an unqualified label. Keep private identifiers and sensitive content out unless they are necessary and authorized for training.

A conceptual JSON record could contain `case_id`, `state`, `allowed_options`, `label`, `rubric_version` and `split_group`. This is an experiment schema, not a universal training-file format. The eventual trainer may require chat messages, tokenized examples or another representation; convert from the reviewed source records with a deterministic script.

Do not place the answer in a state field that the deployed model would not receive. A field named `resolved_queue` can accidentally leak the label into training and evaluation. Review preprocessing with the same care as model selection.

## Split before optimizing

Keep all variants of a source case in one split. If the same incident appears in many tickets, split by incident rather than individual ticket. For a system exposed to changing products or policies, consider a time-based test set to reveal version drift. Record the split procedure so another person can reproduce it.

Start with a rules baseline and an unmodified model. A fine-tune is justified when it improves the metric that matters without unacceptable regressions. For a bounded router, that might be fewer wrong automatic routes at the same review coverage. For generation, include content quality and unsupported claims rather than evaluating only whether JSON parses.

## Do not train confidence by wishful prompting

A generated number labeled confidence is not automatically calibrated. After training, evaluate probability quality separately and choose thresholds on development data. If the serving API exposes only generated text rather than token probabilities, document exactly how the reported score is obtained and what evidence supports interpreting it.

Store the training recipe, base-model identifier, data version, adapter artifact and evaluation results together. A model file without those records is difficult to audit or safely replace. Keep deletion and retention procedures for training data separate from the code repository.

## What the public lab provides

[Agent Decision Lab](https://github.com/Sandeep-BA/agent-decision-lab) includes a `fine-tuning-readiness-coach` recipe and synthetic evidence fields. It does not train a model, distribute customer data or claim that fixture probabilities are learned predictions. The recipe helps review whether a proposed experiment is sufficiently specified.

Before investing in GPUs, estimate dataset size, sequence length, batch behavior and serving requirements for the exact model you selected. Hardware advice without those constraints is guesswork. The deliverable to seek first is a reproducible baseline and a defensible evaluation, not simply a successful training run.
