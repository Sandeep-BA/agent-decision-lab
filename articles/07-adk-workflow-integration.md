# Put typed decisions inside ADK workflows without moving policy into prompts

Author: Sandeep Belgavi · Reviewed 18 October 2026

An agent framework coordinates work; a decision model supplies one kind of judgment. Keeping those roles separate makes the system easier to test and replace. You should be able to change the decision provider without changing the rules for resource access, cancellation, approval or delivery.

<!-- diagram:Scoped workflow|Evidence collection|Independent assessments|Deterministic join|Review gate|Delivery -->

## Choose control flow from dependencies

The [ADK workflow documentation](https://adk.dev/agents/workflow-agents/) describes sequential, parallel and loop execution patterns. It also notes that newer graph workflows apply in some language versions. Check the documentation and source for the exact language and version you install rather than assuming Python, Java and a community fork expose identical APIs.

Use a sequential workflow when the next step requires the previous result. For example, retrieve permitted evidence, draft a response, then validate that response. Parallel execution is appropriate when checks are independent, such as reviewing two different evidence sources. A loop needs an explicit termination condition and a hard resource limit; “keep improving until good” is not a bounded operational contract.

The Java examples in Agent Decision Lab are framework-independent. They do not claim to include a tested ADK plugin. That is deliberate: the policy engine and provider adapter can first be tested in isolation, then wrapped in the framework version used by your application.

## A release-review example

A release-review workflow can collect a test summary and a change summary independently. It then joins those results under one operation identifier. The decision step assesses whether the combined evidence supports a recommendation. A deterministic gate checks required approvals, release identifiers and the requested target environment.

Do not let a parallel child update a shared `approved` flag that another child treats as final authority. Store each child's result under a distinct key and let one join step validate completeness. If a child times out, represent that as missing evidence. A missing check must not be silently converted into a successful check because other children finished.

## Keep custom agents narrow

A custom orchestration component is useful when ordinary sequential or parallel composition cannot express the needed join, cancellation or retry behavior. It should manage workflow state, not invent a second model-driven permission system. Put server-derived identity, budgets and operation state in a context object whose ownership is clear.

If a framework callback intercepts tool calls, verify exactly when it runs and what errors it can suppress. A callback is only a control if every relevant execution path passes through it. Direct tool invocation, retry code and deployment scripts may bypass the normal agent path, so the actual tool gateway must enforce its own authorization.

## Explain model selection per step

A generator may need a general language model, while a narrow route selection can use a typed decision adapter. Deterministic arithmetic and identifier checks should remain code. Record the reason for the selection, such as required modality, local execution, acceptable latency or evaluated decision quality. Avoid choosing a provider merely because it is the default in a framework example.

Test substitutions through the same interface. An adapter that returns the expected Java record can still produce different uncertainty, refusal and error behavior. Preserve those differences instead of flattening every outcome into `success`.

## Verify the assembled workflow

Create integration cases for a failed child, a stale result, a changed proposal after approval, duplicate completion and cancellation during a provider call. Assert that the final delivery gate sees the actual generated output, not just the original request. Audit every delivered result and mark incomplete runs explicitly.

Start with the [100 recipe catalog](https://github.com/Sandeep-BA/agent-decision-lab/blob/main/CATALOG.md) as a set of bounded tasks. Treat the diagram above as a proposed composition pattern. A framework-specific implementation should add its own pinned dependency, executable integration test and deployment evidence before claiming ADK support.
