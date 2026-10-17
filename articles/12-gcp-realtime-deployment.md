# Design a GCP deployment for decisions, approvals and realtime progress

Author: Sandeep Belgavi · Reviewed 18 October 2026

Moving a local agent into a hosted service introduces identity, concurrency, persistence and failure recovery. A process that reads a local environment variable and prints a result is not yet a multi-user application. Treat deployment as a separate engineering phase with its own acceptance tests and operational ownership.

<!-- diagram:Authenticated client|Cloud Run gateway|Budget and operation ledger|Decision worker|Approval and executor|Progress history -->

## Separate the browser session from service identity

The browser authenticates the user through the application's chosen identity provider. The gateway verifies that identity and resolves account scope from trusted data. Internal services should use dedicated service identities with only the necessary permissions. Google documents authenticated [service-to-service calls on Cloud Run](https://cloud.google.com/run/docs/authenticating/service-to-service); use that mechanism according to your deployment rather than forwarding arbitrary browser tokens between services.

Never expose a provider API key in client JavaScript. A server-side worker should retrieve the key from a controlled secret store. The client sends the authorized task, not a provider destination or unrestricted tool command.

## Give persistent stores distinct responsibilities

One proposed architecture uses Cloud SQL for an operation ledger and Firestore for conversation and progress history. The ledger tracks operation identifiers, budget reservations, proposal digests, approval state and effect status. History supports the interface but does not become the source of authority for payments, deployment or access changes.

This is an application design choice, not a requirement to use both databases. A simpler service may use one suitable store. What matters is that the system can answer whether an operation was authorized, whether it was attempted and whether the external outcome is known after a worker restarts.

Use transactional updates or other explicit concurrency controls for budget reservations and idempotency. Two workers must not both see the same available budget and independently spend it. A client-generated retry should reuse an operation identifier only when it represents the same intended action.

## Realtime transport carries progress, not authority

WebSockets can deliver status changes and interactive responses. Google's [Cloud Run WebSocket guidance](https://cloud.google.com/run/docs/triggering/websockets) describes operational constraints that require reconnect and state-synchronization planning. Do not assume a long-lived connection guarantees that all later events come from the same process or that a disconnected client cancelled the underlying job.

Persist progress with monotonically ordered event identifiers and let reconnecting clients resume from the last acknowledged event. Verify authorization again when subscribing to an operation's stream. A guessed operation identifier must not reveal another user's prompts, outputs or approval requests.

For voice or bidirectional systems, distinguish partial transcripts from committed user instructions. An interim recognition result should not trigger an irreversible effect. Bind approval to a displayed, stable proposal after the necessary validation, and handle corrections without reusing stale approval.

## Make deployment evidence concrete

Before release, test unauthorized access, cross-account reads, duplicate requests, provider timeouts, worker restarts and client reconnects. Inspect whether budget reservations are released or reconciled when a job fails. Validate that every delivered result has an audit event and that sensitive raw evidence is not copied into generic logs.

Track user-visible latency separately from model latency. Include queue time, cold starts, database access and approval delays. Define service objectives around accepted outcomes and recovery behavior rather than a single optimistic inference measurement.

## Scope of the reference code

The [Java repository](https://github.com/Sandeep-BA/agent-decision-lab) is a local recommendation runtime with an optional provider call. It does not deploy Cloud Run, create Cloud SQL or Firestore resources, implement login, or serve WebSockets. The diagram is a proposed deployment architecture for readers to implement with their own identities, budgets and infrastructure review.

Keeping that distinction explicit makes the example reusable. A developer can test the decision contract locally, then add deployment components one at a time and publish evidence for each new boundary instead of assuming that a successful command-line demo is production readiness.
