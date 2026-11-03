// Package budget shows how ADK Go v2.7.0 enforces RunConfig.MaxLLMCalls.
//
// Author: Sandeep Belgavi
//
// A scripted model stands in for a real one: it asks for the check_stock tool
// on every turn and never gives a final answer, so the agent loop only stops
// when the model-call budget does. No provider is called.
package budget

import (
	"context"
	"errors"
	"fmt"
	"iter"

	"google.golang.org/adk/v2/agent"
	"google.golang.org/adk/v2/agent/llmagent"
	"google.golang.org/adk/v2/model"
	"google.golang.org/adk/v2/runner"
	"google.golang.org/adk/v2/tool"
	"google.golang.org/adk/v2/tool/functiontool"
	"google.golang.org/genai"
)

// loopingModel requests a tool call on every turn and counts the calls it receives.
type loopingModel struct{ calls int }

func (m *loopingModel) Name() string { return "scripted-looping-model" }

func (m *loopingModel) GenerateContent(ctx context.Context, req *model.LLMRequest, stream bool) iter.Seq2[*model.LLMResponse, error] {
	return func(yield func(*model.LLMResponse, error) bool) {
		m.calls++
		call := &genai.FunctionCall{
			ID:   fmt.Sprintf("call-%d", m.calls),
			Name: "check_stock",
			Args: map[string]any{"isbn": "978-0-00-000044-0"},
		}
		yield(&model.LLMResponse{
			Content:      &genai.Content{Role: "model", Parts: []*genai.Part{{FunctionCall: call}}},
			FinishReason: genai.FinishReasonStop,
		}, nil)
	}
}

type stockArgs struct {
	ISBN string `json:"isbn"`
}

type stockResult struct {
	ISBN    string `json:"isbn"`
	InStock int    `json:"in_stock"`
}

// Outcome records what one run did.
type Outcome struct {
	ModelCalls  int  // calls the model actually received
	BudgetStop  bool // the run ended with an error wrapping agent.ErrLLMCallsLimitExceeded
	OtherError  error
	EventsSeen  int
	Interrupted bool // the caller stopped iterating after a safety cap
}

// Run executes one invocation with the given MaxLLMCalls. safetyCap stops a run
// that would otherwise never end (used for the "no limit" cases).
func Run(ctx context.Context, maxLLMCalls, safetyCap int) (Outcome, error) {
	m := &loopingModel{}
	stock, err := functiontool.New(functiontool.Config{
		Name:        "check_stock",
		Description: "Returns the number of copies in stock for an ISBN at Belgavi's Book Store.",
	}, func(_ agent.Context, a stockArgs) (stockResult, error) {
		return stockResult{ISBN: a.ISBN, InStock: 3}, nil
	})
	if err != nil {
		return Outcome{}, err
	}
	a, err := llmagent.New(llmagent.Config{
		Name:        "stock_helper",
		Description: "Answers stock questions for the help desk.",
		Instruction: "Check stock before answering.",
		Model:       m,
		Tools:       []tool.Tool{stock},
	})
	if err != nil {
		return Outcome{}, err
	}
	r, err := runner.NewInMemory("budget_demo", a)
	if err != nil {
		return Outcome{}, err
	}
	msg := genai.NewContentFromText("Is ISBN 978-0-00-000044-0 in stock? (CASE-4401)", "user")
	var out Outcome
	for ev, err := range r.Run(ctx, "jenya", "session-1", msg, agent.RunConfig{MaxLLMCalls: maxLLMCalls}) {
		if err != nil {
			if errors.Is(err, agent.ErrLLMCallsLimitExceeded) {
				out.BudgetStop = true
			} else {
				out.OtherError = err
			}
			break
		}
		if ev != nil {
			out.EventsSeen++
		}
		if m.calls >= safetyCap {
			out.Interrupted = true
			break
		}
	}
	out.ModelCalls = m.calls
	return out, nil
}
