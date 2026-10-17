# Use typed decisions to review RAG evidence without inventing certainty

Author: Sandeep Belgavi · Reviewed 18 October 2026

Retrieval-augmented generation has at least three distinct failure points: retrieving the wrong evidence, generating an unsupported claim, and presenting a citation that does not support the claim beside it. A single relevance score cannot validate all three. Build separate checks with observable inputs and outputs.

<!-- diagram:Authorized retrieval|Passage selection|Draft generation|Claim source pairs|Support review|Delivery gate -->

## Scope retrieval before relevance

The retrieval system should enforce tenant and resource permissions before returning passages. A passage can be highly relevant and still be unauthorized. Do not ask the model to decide whether it is allowed to see a document after the document has already been sent to it.

Preserve source identifiers, versions and exact passage boundaries. If the draft later cites a source, the system should be able to retrieve the same evidence used during generation. A link to a frequently changing page is not a complete evidence record for a historical decision.

The [TypeSafe citation-check cookbook](https://docs.typesafe.ai/cookbooks/citation_check) demonstrates a bounded support judgment. The design below separates that model-assisted judgment from deterministic checks and does not claim that a verifier eliminates unsupported answers.

## A worked claim review

Suppose a draft says that a service retains audit records for 90 days. The retrieved passage says that records are retained for at least 30 days, with longer retention available on selected plans. A relevance check may rate the passage highly because it discusses retention. A support check should recognize that the specific 90-day claim is not established by that evidence.

Create one review unit containing the claim, the exact cited passage and the relevant qualification. Ask whether the passage supports the claim as written, contradicts it, or leaves it unresolved. Keep an unresolved outcome available. Forcing every case into supported or contradicted misrepresents incomplete evidence.

Then apply deterministic citation checks: the cited source exists in the authorized retrieval set, the passage identifier resolves, and quoted text matches the stored source. These checks are inexpensive and should not be delegated to a probabilistic model.

## Avoid verification by repetition

Asking the same model the same broad question twice is not independent verification. The second answer can repeat the first error, especially if it sees the original explanation as authoritative context. Give the verifier the claim and evidence, not an instruction to agree with the draft's reasoning.

When comparing different verifiers, use the same labeled claim-source pairs. Include partial support, reversed conditions, outdated versions and numerical qualifiers. A dataset consisting only of obviously unrelated passages will overstate usefulness on real documentation questions.

The `citation-support-checker`, `retrieval-sufficiency-gate` and `output-delivery-reviewer` recipes illustrate three different decision locations. They share a runtime but require different evidence. Their offline tests verify that those fields are required and minimized; they do not measure factuality performance.

## Decide what happens after rejection

An unsupported claim can be removed, rewritten to reflect uncertainty, or sent for additional retrieval. The application should not silently swap the citation while leaving the claim unchanged. If the missing fact is central to the user's question, a clear statement of uncertainty may be more useful than a polished answer assembled from weak evidence.

Bound the repair loop. Record the rejected claim, the reason category and the next permitted operation. Avoid logging full sensitive documents when a source identifier and access-controlled evidence reference are sufficient. Keep final delivery behind a check of the actual revised text.

## Measure outcomes that matter

Report unsupported-claim rate, false rejection rate, review coverage and answer completeness on a held-out set. Track failures by source type and document version. A system that removes every substantive claim can achieve a low unsupported-claim rate while failing the user's task.

The [Java source](https://github.com/Sandeep-BA/agent-decision-lab) provides the review boundary and synthetic examples. A production RAG implementation still needs retrieval, source storage, citation parsing and a labeled evaluation suited to its own documents.
