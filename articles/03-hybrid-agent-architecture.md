# A hybrid agent architecture that keeps decisions separate from effects

Author: Sandeep Belgavi · Reviewed 18 October 2026

A practical hybrid system can use a language model to draft, a decision model to classify, and ordinary code to enforce permissions. The useful separation is between proposing an action and possessing authority to execute it. A model response must never be the only thing that establishes the caller's identity, account scope or spending budget.

<!-- diagram:Identity and scope|Budget reservation|Minimized evidence|Model decision|Validation and approval|Effect ledger -->

## Start at the gateway

The gateway validates an authenticated principal and resolves the tenant and resource scope from server-side data. A browser-supplied `tenantId` is a requested resource identifier, not proof of membership. The gateway checks the requested operation, reserves a bounded budget and records an operation identifier before scheduling expensive work.

Only then should the system gather evidence. Retrieval must be scoped independently of the model. If the user cannot read a document, giving the model instructions not to reveal it is not sufficient protection; the document should never enter the model's state. The same applies to credentials and unrelated customer records.

The [TypeSafe System One documentation](https://docs.typesafe.ai/concepts/system-one) provides the decision interface. The surrounding gateway, evidence store and action ledger in this article are proposed application components, not claims about TypeSafe's hosted infrastructure.

## Place generation where generation is needed

Consider a release-review agent. A language model can summarize a verified change set into a review draft. A bounded decision step can assess whether the draft includes required evidence. Deterministic checks should verify build identifiers, required approvals and deployment targets. The model should not estimate whether a checksum matches or whether a user has a production role.

After generation, validate the output again. A pre-generation screen cannot establish what the generator will actually produce. Check output shape, unsupported claims, sensitive-data leakage and compatibility with the delivery channel. A successful input check is only one checkpoint in the workflow.

## Approval binds to an exact proposal

A human approval record should name the operation, target, parameter digest and expiry. If a model changes the proposed target after approval, the approval no longer covers the request. Do not store a global boolean such as `approved=true` in session history and reuse it for every later action.

For effects such as deployment or refund submission, the executor independently checks identity, policy, approval and idempotency. The executor records a durable attempt before calling the external service and reconciles uncertain outcomes. A timeout can mean the service completed the action but the response was lost; blindly retrying may duplicate the effect.

## Explain the storage roles

A proposed GCP deployment might use a Cloud Run gateway, a transactional Cloud SQL ledger for operation state, and Firestore for user-visible conversation history. Those stores have different responsibilities. Chat history is not an authoritative financial ledger, and a log entry is not necessarily a durable transaction record. Store only the data each component needs and define retention separately.

The exact database choice depends on throughput, consistency and operational requirements. The important property is that effect authorization and reconciliation survive a process restart. The local Java example uses only an in-memory trace and therefore does not satisfy that production requirement.

## Validate the boundary before adding autonomy

Test an unauthorized scope, exhausted budget, missing evidence, malformed distribution, low confidence, revoked approval and repeated operation identifier. For each case, record whether the provider ran and whether any business effect occurred. Do not infer success from a fluent final message.

The [Java engine](https://github.com/Sandeep-BA/agent-decision-lab/blob/main/src/main/java/com/belgavi/agents/Engine.java) implements a teaching subset: scope checks, one-call budgeting, field minimization, validation, recommendation approval and a trace. It deliberately has no effect executor. The diagram is a target architecture to implement and test, not deployed infrastructure.
