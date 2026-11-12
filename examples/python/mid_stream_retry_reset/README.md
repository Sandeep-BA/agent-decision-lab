# Mid-stream retries without phantom tool calls

**Author: Sandeep Belgavi**

A runnable companion to *Mid-Stream Retries: Discard the Abandoned Attempt, Including Its Tool Calls* (aicassindra.com). Three accumulation policies (naive, reset on retry, reset with execution after finish) on one synthetic broken stream, plus an effect key derived from the turn and call content.

## Prerequisites

- Python 3.11 or newer. Standard library only. No provider is called.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

`STREAM` in retry_stream.py: attempt 1 emits a refund call and half a sentence, a retry event follows, attempt 2 emits a refund call with a different id and finishes.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Five tests pass. Naive: concatenated text and 2 refunds executed. Reset: clean text, still 2 refunds. Reset with late execution: 1 refund, from attempt 2. The two provider ids produce one content key.

## Limitations

Hand-written events, not a provider wire format. Real streams have more event types and SDKs may retry internally.

Views are my own and do not represent any employer, past or present.
