# Python examples

**Author: Sandeep Belgavi**

Small, self-contained Python programs that accompany the agent architecture guides on
aicassindra.com. Each directory is independent, uses only the Python standard library
(3.11 or newer), ships synthetic fixtures, and has its own README, tests and limitations.
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

Run the commands from the repository root. The Java recipes in `src/` are unaffected by
this directory; nothing here is built by Maven.
