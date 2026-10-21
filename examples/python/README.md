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

Run the commands from the repository root. The Java recipes in `src/` are unaffected by
this directory; nothing here is built by Maven.
