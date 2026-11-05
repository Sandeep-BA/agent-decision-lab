# Python examples

**Author: Sandeep Belgavi**

Small, self-contained Python programs that accompany the agent architecture guides on
aicassindra.com. Each directory is independent, uses the Python standard library unless its
`requirements.txt` pins a package (3.11 or newer), ships synthetic fixtures, and has its own README, tests and limitations.
None of them calls a model provider; they exercise the runtime mechanics around an agent.

| Example | Guide | Run the tests |
| --- | --- | --- |
| [`agent_outbox_journal`](agent_outbox_journal/) | Agent tool effects through a transactional outbox | `python -m unittest discover -s examples/python/agent_outbox_journal -p "test_*.py"` |
| [`durable_replay_agent`](durable_replay_agent/) | Durable execution for agent workflows: replay determinism | `python -m unittest discover -s examples/python/durable_replay_agent -p "test_*.py"` |
| [`model_request_hooks`](model_request_hooks/) | Observation-only hooks around model requests | `python -m unittest discover -s examples/python/model_request_hooks -p "test_*.py"` |
| [`agent_tool_contracts`](agent_tool_contracts/) | Testing a service once an agent calls it: consumer contracts, replays, invariants | `python -m unittest discover -s examples/python/agent_tool_contracts -p "test_*.py"` |
| [`online_eval_mix_shift`](online_eval_mix_shift/) | Online evaluation: traffic mix shift versus quality drop | `python -m unittest discover -s examples/python/online_eval_mix_shift -p "test_*.py"` |
| [`agent_event_consumer`](agent_event_consumer/) | An agent step inside an existing event consumer: per-key order, 429 backpressure, parking, redelivery | `python -m unittest discover -s examples/python/agent_event_consumer -p "test_*.py"` |
| [`agent_sql_gate`](agent_sql_gate/) | Letting an agent query an existing database: a capability gate from SQLite hooks | `python -m unittest discover -s examples/python/agent_sql_gate -p "test_*.py"` |
| [`batch_submission_ledger`](batch_submission_ledger/) | Provider batch APIs: a submission ledger with custom_id reconciliation and resubmission | `python -m unittest discover -s examples/python/batch_submission_ledger -p "test_*.py"` |
| [`tenant_fair_queue`](tenant_fair_queue/) | Agent traffic on shared internal services: per-tenant fair queuing and an agent call budget | `python -m unittest discover -s examples/python/tenant_fair_queue -p "test_*.py"` |
| [`residual_router`](residual_router/) | Rules first, agent for the residual: router, validator and acceptance threshold | `python -m unittest discover -s examples/python/residual_router -p "test_*.py"` |
| [`prompt_cache_audit`](prompt_cache_audit/) | Prompt caching in agent loops: prefix breakers, breakpoints and TTL gaps | `python -m unittest discover -s examples/python/prompt_cache_audit -p "test_*.py"` |
| [`agent_commit_token_reads`](agent_commit_token_reads/) | Verifying an agent’s own write: replica lag, commit tokens and intent keys | `python -m unittest discover -s examples/python/agent_commit_token_reads -p "test_*.py"` |
| [`embedding_migration_shadow`](embedding_migration_shadow/) | Changing embedding models: overlap at k, recall at k, rank fusion and backfill gaps | `python -m unittest discover -s examples/python/embedding_migration_shadow -p "test_*.py"` |
| [`bitemporal_memory`](bitemporal_memory/) | Bitemporal agent memory: valid time, record time, corrections and erasure | `python -m unittest discover -s examples/python/bitemporal_memory -p "test_*.py"` |
| [`async_job_endpoint`](async_job_endpoint/) | An agent step behind an endpoint: 202 Accepted, a job resource, Idempotency-Key and one credit per request | `python -m unittest discover -s examples/python/async_job_endpoint -p "test_*.py"` |
| [`agent_cost_forecast`](agent_cost_forecast/) | Forecasting an agent feature's token cost from a pilot and checking it against week one | `python -m unittest discover -s examples/python/agent_cost_forecast -p "test_*.py"` |
| [`reasoning_state_passthrough`](reasoning_state_passthrough/) | Passing reasoning state back across tool calls through a provider-neutral transcript store | `python -m unittest discover -s examples/python/reasoning_state_passthrough -p "test_*.py"` |
| [`change_event_loop_guard`](change_event_loop_guard/) | Origin filters, no-op suppression and hop limits for agents subscribed to change events they can cause | `python -m unittest discover -s examples/python/change_event_loop_guard -p "test_*.py"` |
| [`streamed_tool_call_assembler`](streamed_tool_call_assembler/) | Assembling streamed tool-call arguments from Claude, OpenAI Responses and Gemini Interactions events, with an execution gate | `python -m unittest discover -s examples/python/streamed_tool_call_assembler -p "test_*.py"` |
| [`tokenizer_count_compare`](tokenizer_count_compare/) | The same texts under five public tokenizers at pinned revisions, and a per-kind projection for a model switch | `python -m unittest discover -s examples/python/tokenizer_count_compare -p "test_*.py"` |
| [`agent_cache_invalidation`](agent_cache_invalidation/) | Cache-aside invalidation when an agent writes around the service: direct writes, change-stream invalidation and a versioned tombstone against slow refills | `python -m unittest discover -s examples/python/agent_cache_invalidation -p "test_*.py"` |
| [`agent_bulk_change_job`](agent_bulk_change_job/) | A previewed bulk change: declarative spec, manifest hash approval, version-checked batches and resume | `python -m unittest discover -s examples/python/agent_bulk_change_job -p "test_*.py"` |
| [`eval_trial_isolation`](eval_trial_isolation/) | Shared versus per-trial databases in agent evaluation, and a start-state fingerprint that catches leaks | `python -m unittest discover -s examples/python/eval_trial_isolation -p "test_*.py"` |
| [`scheduled_followup_dst`](scheduled_followup_dst/) | Agent-scheduled follow-ups stored as wall-clock time plus IANA zone: repeated and missing hours, fire-time re-check and idempotent sends | `python -m unittest discover -s examples/python/scheduled_followup_dst -p "test_*.py"` |
| [`expand_contract_rename`](expand_contract_rename/) | Expand-contract column rename with agent tools on both names: sync triggers, old-write log, reference scanner and contract gate | `python -m unittest discover -s examples/python/expand_contract_rename -p "test_*.py"` |
| [`shared_spend_limit`](shared_spend_limit/) | One token budget shared by concurrent runs: check-then-spend overshoot against reserve-and-settle | `python -m unittest discover -s examples/python/shared_spend_limit -p "test_*.py"` |
| [`legacy_acl`](legacy_acl/) | An anti-corruption layer for agent tools over a legacy back office: code and unit translation, unwritten invariants and an idempotent refund | `python -m unittest discover -s examples/python/legacy_acl -p "test_*.py"` |
| [`stuck_loop_detector`](stuck_loop_detector/) | Detecting stuck agent loops from normalised call and result fingerprints and a progress signal, with a polling exemption | `python -m unittest discover -s examples/python/stuck_loop_detector -p "test_*.py"` |
| [`eval_noise`](eval_noise/) | Task, generation and grader variance in an eval score from repeated generations and re-grades, and the resulting half-widths | `python -m unittest discover -s examples/python/eval_noise -p "test_*.py"` |
| [`write_skew_guard`](write_skew_guard/) | Write skew between concurrent agent runs: a quota-row write tool against a read-then-insert pair | `python -m unittest discover -s examples/python/write_skew_guard -p "test_*.py"` |
| [`undo_window`](undo_window/) | An undo window for agent actions: conditional cancel and claim, idempotent execution | `python -m unittest discover -s examples/python/undo_window -p "test_*.py"` |
| [`tool_selection_regression`](tool_selection_regression/) | Tool descriptions as prompts: recorded selection runs, per-case diffs and new failures | `python -m unittest discover -s examples/python/tool_selection_regression -p "test_*.py"` |
| [`table_row_chunks`](table_row_chunks/) | Tables in a retrieval corpus: row serialization with headers and a strict answerability check | `python -m unittest discover -s examples/python/table_row_chunks -p "test_*.py"` |
| [`model_fallback_refusal_policy`](model_fallback_refusal_policy/) | Refusals and ModelFallback in pydantic-ai 2.65: the default and an explicit stop policy, pinned by tests (needs `pip install -r requirements.txt`) | `python -m unittest discover -s examples/python/model_fallback_refusal_policy -p "test_*.py"` |
| [`run_keyed_sampling`](run_keyed_sampling/) | Sampling whole agent runs: explicit randomness from the run id instead of per-trace decisions | `python -m unittest discover -s examples/python/run_keyed_sampling -p "test_*.py"` |
| [`graphql_operation_tools`](graphql_operation_tools/) | Agents calling a GraphQL API: registered operations as tools, a per-run cost budget and partial results | `python -m unittest discover -s examples/python/graphql_operation_tools -p "test_*.py"` |
| [`tool_definition_budget`](tool_definition_budget/) | What tool definitions cost per request: token counts and cache arithmetic (needs `pip install -r requirements.txt`) | `python -m unittest discover -s examples/python/tool_definition_budget -p "test_*.py"` |
| [`structured_output_eval`](structured_output_eval/) | Schema-constrained output on small local models: validity versus correctness, with recorded Ollama runs | `python -m unittest discover -s examples/python/structured_output_eval -p "test_*.py"` |
| [`identifier_canonical_keys`](identifier_canonical_keys/) | Unicode usernames: a canonical key for uniqueness and a confusables skeleton for review | `python -m unittest discover -s examples/python/identifier_canonical_keys -p "test_*.py"` |
| [`sqs_partial_batch`](sqs_partial_batch/) | Lambda and SQS: partial batch responses, poison messages and FIFO order | `python -m unittest discover -s examples/python/sqs_partial_batch -p "test_*.py"` |

Run the commands from the repository root. The Java recipes in `src/` are unaffected by
this directory; nothing here is built by Maven.

A Go example, [`../go/llm_call_budget`](../go/llm_call_budget/), tests model-call budgets in ADK Go v2.7.0 with `go test` (Go 1.26.10 or newer).
