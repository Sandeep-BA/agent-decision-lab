# Route between rules, local SLMs and hosted models using measured constraints

Author: Sandeep Belgavi · Reviewed 18 October 2026

A model router is useful only if it improves an application objective. Sending simple requests to a cheaper model sounds reasonable, but the routing call, retries, review workload and extra latency can erase the savings. Measure the complete path from accepted request to acceptable result.

<!-- diagram:Task constraints|Deterministic checks|Candidate route|Quality evaluation|Cost and latency ledger -->

## Begin with hard constraints

Some routing decisions do not require a model. A request that must stay on-device cannot be sent to a hosted endpoint. A request requiring audio or image processing must use a supported modality. An exhausted account budget must stop expensive work even if the router believes a premium model would answer well.

Represent these conditions in code before semantic routing. Then compare candidates that satisfy them. Jev can supply a bounded decision through its documented interface, while a local SLM can generate or classify depending on its training and runtime. Neither category establishes suitability by itself.

The [TypeSafe model documentation](https://docs.typesafe.ai/models) is the source for provider versions and limits. For a local model, use its own model card and runtime documentation. Do not copy context sizes or hardware claims from a different quantization or model family.

## A worked cascade

Suppose an application receives short documentation questions. Exact account and entitlement checks run first. A retrieval step gathers permitted passages. A small local model attempts an answer, then a bounded verifier checks whether the answer is supported. If evidence is weak, the system asks for clarification or escalates to a larger model under a reserved budget.

A cascade should not retry until something passes. Set a maximum number of model calls and a deadline for the entire request. Decide in advance whether a failed verifier leads to review, another retrieval attempt or a larger model. The path should be understandable from a trace without reconstructing hidden prompt logic.

In the Java engine, the one-call budget is an intentionally small teaching limit. A production cascade needs a durable budget reservation shared across concurrent requests. A local integer passed by the caller does not prevent multiple processes from spending the same allowance.

## Calculate the complete cost

For each request, include routing, generation, verification, retry and human-review costs. If the average routing cost is R, the first model cost is S and the escalation probability is p with escalation cost L, an elementary expected provider cost is R + S + pL. Add other stages and infrastructure costs explicitly rather than hiding them in a headline percentage.

This expression is a planning model, not a measured benchmark. Independence assumptions may fail: difficult requests can simultaneously consume more tokens, trigger retries and require review. Use traces to estimate the joint distribution once the system has representative traffic.

Measure latency at the user boundary. Report median and tail behavior, queue time, cold starts, network time and timeout rates. A fast isolated inference call can sit inside a slow application. For on-device models, include model loading, memory pressure and contention with the user's other applications.

## Compare accepted outcomes

Run every candidate on the same frozen tasks and evidence. Report quality at comparable review coverage, not only average accuracy. A route that sends most difficult cases to humans should not be compared with a fully automated route without showing that difference.

Include malformed output, refusal, unavailable provider and insufficient evidence as explicit outcomes. They affect reliability and cost even when there is no final answer to score. Keep model version, prompt version and quantization in the experiment record.

The `model-routing-reviewer` recipe in [Agent Decision Lab](https://github.com/Sandeep-BA/agent-decision-lab) helps review a stated model choice against supplied constraints. It is not an automatic benchmark or a deployed router. Its value is making the selection rationale inspectable before a more complex cascade is implemented.
