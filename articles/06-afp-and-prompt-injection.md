# Abuse and fraud prevention needs controls outside the model

Author: Sandeep Belgavi · Reviewed 18 October 2026

An abuse-and-fraud-prevention system should separate suspicious-content judgment from permission enforcement. A model can help prioritize ambiguous evidence. It should not decide whether the caller possesses a valid session, whether a resource belongs to that caller, or whether an external effect has already been executed. Those checks belong in trusted application code.

<!-- diagram:Untrusted content|Scope and minimization|Risk assessment|Policy enforcement|Human review|Audited result -->

## How the trust boundary is crossed

Prompt injection occurs when content supplied as data influences the assistant as though it were authorized instructions. A retrieved page might ask the assistant to reveal private information or change its tool behavior. The important defect is not merely that the text is persuasive; it is that the application gives that text a path to authority it should not have.

In a database assistant, a row containing instructions remains a row. A read-only database role prevents database writes, but it does not prevent the assistant from disclosing data through another tool. Review the entire capability set and data flow, not only the prompt used by the database tool.

TypeSafe's [documented Jev limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13) include adversarial-content and instruction-related limitations for that version. A typed response format therefore must not be presented as proof that prompt injection is solved.

## A concrete support workflow

Imagine a support agent reading a customer-supplied attachment before drafting a refund recommendation. First authenticate the operator and resolve the customer's account scope. Retrieve only the records needed for the case. Strip unrelated fields before inference, and keep the refund policy separate from the attachment.

A decision model can flag whether the attachment attempts to redirect the workflow, but an unflagged attachment must still have no authority to trigger payment. The executor should require a verified account, exact amount calculated in code, policy eligibility and an approval record bound to that proposal. If any of those checks fails, the effect stops regardless of the model's risk score.

The example `fraud-case-prioritizer` recipe produces a recommendation for human review. It does not freeze accounts, accuse a customer of fraud or calculate liability. Its fixture probabilities are synthetic, so they cannot be used as evidence of fraud-detection quality.

## Evaluate both misses and false alarms

A defensive test set needs benign content that resembles an attack as well as malicious-looking attempts to change behavior. Documentation might legitimately quote a dangerous instruction for analysis. If every quoted instruction is blocked, the product becomes unusable for security research and ordinary troubleshooting.

Label the intended task, source provenance, authorized tools and expected effect boundary for each case. Evaluate whether the application leaked data or attempted an unauthorized effect, not simply whether the model used a refusal phrase. A correct refusal followed by an unauthorized tool call is still a failed boundary.

Keep test cases synthetic and operate inside owned fixtures. The goal is to verify prevention and detection, not to probe unrelated systems. Record the model and policy versions because a new classifier can change both detection and false-positive rates.

## Layer controls with different failure modes

Use scoped credentials, resource allowlists, egress restrictions, call budgets, schema validation, approval checks and durable audit records. Each layer should answer a specific question. Network policy controls destinations; it does not decide whether a claim is true. A schema validator controls shape; it does not establish user consent. A human reviewer needs evidence and an exact proposal, not an unexplained percentage.

The [Cassandra MCP implementation](https://github.com/Sandeep-BA/cassandra-mcp) demonstrates narrow read tools and explicit table permissions. The [agent engine](https://github.com/Sandeep-BA/agent-decision-lab) demonstrates review and approval states. Neither repository is a certified fraud-prevention product, and neither fixture suite establishes resistance to every adversarial input.
