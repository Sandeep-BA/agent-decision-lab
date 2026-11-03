# Model-call budgets in ADK Go 2.7: MaxLLMCalls semantics under test

**Author: Sandeep Belgavi**

A runnable companion to *Test Agent Model Call Limits Before Upgrading to ADK Go 2.7* (aicassindra.com, ADK).
ADK Go v2.7.0 bounds the model calls one invocation may make with `agent.RunConfig.MaxLLMCalls`. A scripted model
asks for a `check_stock` tool on every turn and never answers, standing in for a stuck Belgavi's Book Store help-desk
agent, so the loop stops only when the budget does. The tests pin five rules read from the v2.7.0 source:

| `MaxLLMCalls` | `ADK_MAX_LLM_CALLS` | Result in the tests |
| --- | --- | --- |
| 3 | unset or empty | stops after exactly 3 model calls with `ErrLLMCallsLimitExceeded` |
| 0 | `x` (not an integer) | ignored; stops after 500 calls |
| 0 | `7` | stops after 7 calls |
| 4 | `7` | the field wins; stops after 4 calls |
| -1 | unset or empty | no limit; the caller stops iterating at 600 calls |

**No model provider is called.** The model is a local Go type implementing `model.LLM`.

## Prerequisites

- Go 1.26.10 or newer (required by `google.golang.org/adk/v2` v2.7.0).
- Network access for the first `go test` to download modules listed in `go.sum`.
- No API key or environment variable; `.env.example` documents that.

## Commands

Run from the repository root.

```
cd examples/go/llm_call_budget
go vet ./...
go test -count=1 -v ./...
```

## Expected output

```
--- PASS: TestLimitOfNAllowsExactlyNCalls
--- PASS: TestZeroMeansDefault500NotUnlimited
--- PASS: TestEnvOverrideAppliesWhenFieldIsZero
--- PASS: TestFieldWinsOverEnv
--- PASS: TestNegativeMeansNoLimit
PASS
```

Timings vary; the 500- and 600-call cases take a few seconds.

## Limitations

- Only the runner path is covered. The source says a run started without the runner has no limit, that
  sub-agents run through `agenttool` get their own budget, and that compaction summaries are not counted; none of
  these is tested here.
- The scripted model returns the same tool call each turn. Real models vary, but the budget counts calls, not content.
- Pinned to v2.7.0. Re-run the tests after upgrading; a change in defaults will fail them.
