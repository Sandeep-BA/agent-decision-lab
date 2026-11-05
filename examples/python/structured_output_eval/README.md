# structured_output_eval

**Author: Sandeep Belgavi**

Companion to the guide *Schema-Constrained Output on a Small Local Model Fixes Syntax, Not Answers*
on aicassindra.com. It extracts four fields from twelve synthetic help-desk messages for Belgavi's Book
Store with a local Ollama model in three modes, then scores the results against hand-written labels.

| Mode | What the request sets |
| --- | --- |
| `prompt` | The schema is in the prompt only |
| `json` | `format: "json"` |
| `schema` | `format: <the JSON schema>` |

- `cases.json`: the twelve messages and their gold labels.
- `schema.py`: the extraction schema and a validator written for exactly this schema.
- `grounding.py`: checks that an extracted order id or amount actually appears in the message.
- `run_eval.py`: `--live` calls Ollama and writes `recordings/<model>.json`; without `--live` it only scores recordings.
- `report.py`: which wrong order ids the schema validator catches, which only grounding catches.
- `recordings/`: the two runs used in the guide (Ollama 0.40.12, temperature 0, seed 7, on Windows).

## Prerequisites

Python 3.11 or newer, standard library only. The offline commands need nothing else. Live runs need a
local Ollama server and the two models (`ollama pull qwen2.5:0.5b-instruct`, `ollama pull qwen2.5:1.5b`);
set `OLLAMA_HOST` if it is not on `http://127.0.0.1:11434` (see `.env.example`). No API key is used.

## Run

Offline, from this directory:

```
python run_eval.py
python report.py
python -m unittest -v
```

Live (overwrites the recording for that model):

```
python run_eval.py --live --model qwen2.5:1.5b
```

Expected offline output is in `expected_output.txt`. The headline numbers:

- `schema` mode: 12 of 12 outputs parse and pass the schema for both models; 3 of 12 (0.5B) and 1 of 12
  (1.5B) have all four fields right.
- `prompt` mode with the 0.5B model: 0 of 12 parse, because every reply is wrapped in a Markdown code fence.
- 1.5B, case `c06`: `prompt` mode returns `BK-000125`, which fails the pattern. `schema` mode returns
  `BK-00012`, which passes it and is still invented. Only the grounding check flags it.

## Limitations

- Twelve cases and two small models are a teaching fixture, not a benchmark. Do not read the field
  accuracies as model quality numbers; they depend on this prompt and these labels.
- Recordings are from one machine and one Ollama version. A live re-run with another version, build or
  hardware may produce different outputs even at temperature 0 with a fixed seed.
- The validator covers only this schema. Use a JSON Schema library for anything larger.
- The grounding check only covers fields whose value should be copied from the text.
