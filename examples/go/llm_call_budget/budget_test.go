// Tests for MaxLLMCalls semantics in ADK Go v2.7.0. Author: Sandeep Belgavi
package budget

import (
	"context"
	"testing"
)

func run(t *testing.T, max, safetyCap int) Outcome {
	t.Helper()
	out, err := Run(context.Background(), max, safetyCap)
	if err != nil {
		t.Fatalf("setup: %v", err)
	}
	if out.OtherError != nil {
		t.Fatalf("unexpected run error: %v", out.OtherError)
	}
	return out
}

func TestLimitOfNAllowsExactlyNCalls(t *testing.T) {
	t.Setenv("ADK_MAX_LLM_CALLS", "")
	out := run(t, 3, 1000)
	if !out.BudgetStop || out.ModelCalls != 3 {
		t.Fatalf("want budget stop after 3 model calls, got %+v", out)
	}
}

func TestZeroMeansDefault500NotUnlimited(t *testing.T) {
	// Unset the override so the built-in default applies.
	t.Setenv("ADK_MAX_LLM_CALLS", "x")
	out := run(t, 0, 2000)
	if !out.BudgetStop || out.ModelCalls != 500 {
		t.Fatalf("want budget stop at 500 (unparsable override ignored), got %+v", out)
	}
}

func TestEnvOverrideAppliesWhenFieldIsZero(t *testing.T) {
	t.Setenv("ADK_MAX_LLM_CALLS", "7")
	out := run(t, 0, 1000)
	if !out.BudgetStop || out.ModelCalls != 7 {
		t.Fatalf("want budget stop at 7 from ADK_MAX_LLM_CALLS, got %+v", out)
	}
}

func TestFieldWinsOverEnv(t *testing.T) {
	t.Setenv("ADK_MAX_LLM_CALLS", "7")
	out := run(t, 4, 1000)
	if !out.BudgetStop || out.ModelCalls != 4 {
		t.Fatalf("want budget stop at 4, got %+v", out)
	}
}

func TestNegativeMeansNoLimit(t *testing.T) {
	t.Setenv("ADK_MAX_LLM_CALLS", "")
	out := run(t, -1, 600)
	if out.BudgetStop || !out.Interrupted || out.ModelCalls != 600 {
		t.Fatalf("want no budget stop; caller cap at 600, got %+v", out)
	}
}
