# Token counts for the same text under five public tokenizers

**Author: Sandeep Belgavi**

A runnable companion to *Same Text, Different Token Counts* (aicassindra.com, LLM). Nine synthetic book-shop
texts (English, JSON, Python, Hindi, Kannada and log lines) are counted under tiktoken `cl100k_base` and
`o200k_base` and under the tokenizer.json files of Qwen2.5-0.5B-Instruct, Phi-3.5-mini-instruct and
DeepSeek-V3 at pinned revisions. `projection.py` turns per-kind ratios into a projected token factor.

**No model or provider API is called.** Counts are raw tokenizer output with no chat template or special
tokens, so billed counts will be somewhat higher. Claude and Gemini tokenizers are not published; use their
count endpoints for those.

## Prerequisites

- Python 3.11 or newer and the pinned packages: `pip install -r examples/python/tokenizer_count_compare/requirements.txt`
- Network once, to fetch three tokenizer.json files from Hugging Face and the two tiktoken encodings.
- No API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/tokenizer_count_compare/fetch_tokenizers.py
python examples/python/tokenizer_count_compare/measure.py
python examples/python/tokenizer_count_compare/projection.py
python -m unittest discover -s examples/python/tokenizer_count_compare -p "test_*.py"
```

Without the packages or fetched files the measurement test is skipped and the three projection tests still run.

## Expected output (measured 2026-10-29 with tiktoken 0.12.0 and tokenizers 0.22.1)

| Sample | cl100k | o200k | Qwen2.5 | Phi-3.5 | DeepSeek-V3 |
| --- | --- | --- | --- | --- | --- |
| English help-desk message | 93 | 93 | 98 | 106 | 93 |
| Order record, compact JSON | 139 | 139 | 168 | 196 | 148 |
| Order record, indented JSON | 217 | 216 | 246 | 295 | 224 |
| Python function | 112 | 111 | 113 | 141 | 120 |
| Hindi message | 149 | 47 | 138 | 163 | 100 |
| Hindi in JSON, ensure_ascii=True | 389 | 389 | 625 | 713 | 389 |
| Hindi in JSON, ensure_ascii=False | 154 | 52 | 143 | 167 | 105 |
| Kannada message | 248 | 49 | 195 | 344 | 98 |
| Eight log lines with ids | 517 | 517 | 661 | 674 | 520 |
| Total | 2,018 | 1,613 | 2,387 | 2,799 | 1,797 |

`projection.py` prints `projected token factor for the article mix: 1.268` (60 percent English, 30 percent
indented JSON, 10 percent Hindi, moving from o200k_base to Qwen2.5).

## Limitations

Nine short texts are an illustration, not a benchmark of any model. Measure your own traffic by kind of
content, and count full requests including tool definitions and system prompts. Model licences differ;
only the tokenizer files are downloaded.
