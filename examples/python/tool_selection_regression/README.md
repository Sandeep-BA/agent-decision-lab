# Tool-selection regression test: fixed cases, versioned descriptions, per-case diffs

**Author: Sandeep Belgavi**

A runnable companion to *Tool Descriptions Are Prompts* (aicassindra.com, agents). Sixteen synthetic help-desk
messages for Belgavi's Book Store, four per tool, and three versions of the tool descriptions. `report` reads the
recorded runs in `recorded/` and prints, per model and version, the number of correct first tool calls and the
cases that newly fail against v1.

The recorded runs were made on 3 November 2026 with Ollama 0.40.12 on one Windows 11 machine, models
qwen2.5:1.5b and qwen2.5:0.5b-instruct, temperature 0, seed 7, three repeats per case. They are small local models;
other models will route differently. **The tests and the default command call no model.** `live` mode calls a local
Ollama server at 127.0.0.1:11434 and needs the model pulled first.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` lists nothing to install.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

Run from the repository root.

```
python examples/python/tool_selection_regression/selection.py
python -m unittest discover -s examples/python/tool_selection_regression -p "test_*.py"
python examples/python/tool_selection_regression/selection.py live qwen2.5:1.5b 3 > run.json   # optional, needs Ollama
```

## Expected output

```
qwen2.5:0.5b-instruct  v1 correct 34/48 new failures vs v1: -
qwen2.5:0.5b-instruct  v2 correct 38/48 new failures vs v1: ['Is ISBN 9780140449136 available?']
qwen2.5:0.5b-instruct  v3 correct 29/48 new failures vs v1: [... four cases ...]
qwen2.5:1.5b           v1 correct 42/48 new failures vs v1: -
qwen2.5:1.5b           v2 correct 42/48 new failures vs v1: []
qwen2.5:1.5b           v3 correct 36/48 new failures vs v1: ['I already mailed back BK-1047 last week, where is my refund?', 'You charged me twice for BK-1055, please refund one charge.']
```

Five unittest cases over the recorded runs: the scores, no change from v2 on the 1.5b model, the two refund cases v3 moves, a higher total that hides a new failure on the 0.5b model, and that the case set matches the code.

## Limitations

Sixteen cases are enough to show the mechanism, not to qualify a production agent. The runner records only the
first tool call, not its arguments. A hosted model is less repeatable than a local one at temperature 0, so run
several repeats and treat cases that change across repeats as unstable.
