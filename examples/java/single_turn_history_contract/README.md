# Single-turn history as an explicit input contract

**Author: Sandeep Belgavi**

A runnable companion to *Make ADK Single-Turn History an Explicit Workflow Input Contract* (aicassindra.com). A standalone model of the rule added in ADK Java commit 8e56693 (released in 1.15.0): a `SINGLE_TURN` LlmAgent workflow node whose `includeContents` was never set runs with no history; an explicit setting, or an agent without a mode, keeps it. Adds a startup check that pins the expected history per node.

## Prerequisites

- A JDK 17 or newer (run here with javac and java 23.0.2). No build tool and no dependencies. It does not depend on or download ADK.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Two synthetic history turns for Jenya and one node input in `HistoryContract`.

## Commands

From this directory:

```
javac --release 17 -d build HistoryContract.java HistoryContractTest.java
java -cp build HistoryContractTest
java -cp build HistoryContract
```

## Expected output

Unset drafter: 3 contents before the change, only the node input after it. Pinned DEFAULT: 3 contents. The pinned contract flags `draft_reply: expected DEFAULT but runs with NONE (setting left unset)` under the new rule and passes once the setting is explicit. `8 checks passed`.

## Limitations

This restates the rule; it is not ADK. Verify against your ADK version with its own tests before relying on it.

Views are my own and do not represent any employer, past or present.
