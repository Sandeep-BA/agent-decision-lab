# Jev, LLMs and SLMs: choose by the decision contract

Author: Sandeep Belgavi · Reviewed 18 October 2026

A useful model comparison begins with the output the application needs. A support workflow might need a paragraph explaining a problem, a choice of support queue, and an exact check that an account belongs to the caller. Those are three different jobs. Putting them behind one chat prompt hides their different correctness requirements.

<!-- diagram:Application task|Required output|Candidate models|Paired evaluation|Bounded deployment -->

## What the names do and do not establish

TypeSafe describes Jev as a System One model for typed decisions. The public API accepts state and a map of questions, then returns answers associated with those questions. That is a useful interface distinction. It does not tell us the parameter count or reveal a reproducible internal network architecture. Do not draw transformer blocks or claim a particular model size without a primary technical disclosure.

An LLM is a language model capable of generating sequences. An SLM generally describes a relatively small language model, with no single industry-wide parameter boundary. A small model can still generate text, and a large model can be constrained to return structured data. Consequently, comparing Jev with an SLM is not simply comparing two sizes of the same product. Compare the task interface, deployment constraints, measured quality and operational cost separately.

The [TypeSafe introduction](https://typesafe.ai/blog/introducing-system-one-models-and-jev) describes its approach and vendor evaluations. Treat the reported performance gains as results under the vendor's conditions, not as a guarantee for your application. The [model documentation](https://docs.typesafe.ai/models) is the source for currently supported versions and limits.

## A worked support example

Suppose a user writes that a scheduled export failed after a plan change. A routing decision needs a small option set: technical investigation, subscription clarification, or human review. The generative response needs a clear explanation using verified account facts. The authorization check needs an exact account identifier comparison against trusted session context.

Use code for authorization. Compare a Jev Choice question, a small local language model with constrained output, and the existing large-model router on the same labeled messages. Keep the allowed queues identical. Measure both incorrect routes and review rates. A router that avoids errors by sending every case to a person is safe in one narrow sense but may not meet the service objective.

After routing, use the selected language model to draft an answer only when enough evidence exists. A deterministic validator checks that the required fields are present; a source-aware review checks whether the answer's claims are supported. The routing result does not grant the draft permission to change the account.

## Local operation is a separate requirement

If the application must run without network access, a hosted Jev endpoint does not satisfy that requirement. A locally deployed SLM might, provided the model license, runtime, memory footprint and quality are appropriate. Conversely, an available GPU does not automatically make a local model cheaper: include idle capacity, operations, upgrades and the volume of accepted answers.

The Java collection deliberately separates `Engine.Model` from policy enforcement. Its fixture implementation gives repeatable outputs for tests, while `JevClient` calls the documented hosted API. There is no local Jev model bundled in the repository, and the fixture is not an SLM. A future local-model adapter must be evaluated as another implementation, not treated as equivalent because it returns the same JSON shape.

## A useful acceptance decision

Write a comparison sheet before running experiments: required output, permitted data location, maximum latency, allowed review rate, and error costs. Use a held-out set with realistic ambiguous cases. Record the exact model version and prompts. Select the simplest candidate that meets those constraints, and keep an explicit fallback when it cannot decide.

The architecture diagram above is an application selection process, not a picture of Jev's internals. The runnable example is [Agent Decision Lab](https://github.com/Sandeep-BA/agent-decision-lab), whose tests verify software boundaries rather than comparative model intelligence.
