# tool_definition_budget

**Author: Sandeep Belgavi**

Companion to the guide *Measure What Tool Definitions Cost on Every Agent Request* on aicassindra.com.

- `catalog.py`: sixteen synthetic help-desk tools for Belgavi's Book Store, each with a concise and a
  verbose description (the verbose one adds the usage notes, error contract and example that tool
  descriptions tend to accumulate).
- `measure.py`: counts tokens of the definitions as compact JSON with tiktoken's `o200k_base` encoding.
- `budget.py`: per-run arithmetic for the tool prefix in input-token equivalents, with and without
  prompt caching, and with mid-run tool-list changes that force a new cache write.

## Prerequisites

Python 3.11 or newer. `pip install -r requirements.txt` (pinned: tiktoken 0.14.0 and its dependencies).
tiktoken downloads the `o200k_base` file on first use; set `TIKTOKEN_CACHE_DIR` (see `.env.example`) to
reuse it offline. No API key is needed and no model is called.

## Run

```
python measure.py
python budget.py
python -m unittest -v
```

Expected output (`expected_output.txt`), measured with Python 3.13.5 and tiktoken 0.14.0:

```
concise  16 tools   1327 tokens  largest [(135, 'create_return'), (133, 'update_address'), (129, 'issue_refund')]  smallest (44, 'get_customer')
verbose  16 tools   3378 tokens  largest [(273, 'create_return'), (259, 'update_address'), (257, 'issue_refund')]  smallest (171, 'get_customer')
always-loaded subset (get_order, list_orders, add_case_note, escalate_case): 830 tokens
concise  12 steps uncached  19356  cached   3791  cached with one tool-list change   5646
verbose  12 steps uncached  43968  cached   8610  cached with one tool-list change  12824
```

The budget lines add a 286-token tool-use system prompt, the figure Anthropic's tool-use page lists for
several current Claude models with `tool_choice` auto. Replace it with your model's figure.

## Limitations

- `o200k_base` is an OpenAI tokenizer. Claude, Gemini and local models tokenize differently, and every
  provider renders tool definitions into its own internal format, so absolute counts differ by provider.
  Use the counts to compare definitions with each other; take absolute numbers from your provider's
  token-counting endpoint or response usage fields.
- The cache arithmetic assumes every request in the run hits the cache after the first. Requests more than
  a TTL apart, prompts below the provider's minimum cacheable length, and changes earlier in the prompt
  all break that assumption.
- The token-count tests are skipped when tiktoken or its encoding file is unavailable; the arithmetic and
  schema tests always run.
