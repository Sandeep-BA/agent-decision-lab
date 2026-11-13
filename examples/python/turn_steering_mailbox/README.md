# Messages sent to a running agent turn

**Author: Sandeep Belgavi**

A runnable companion to *Messages Sent to a Running Agent Turn: Admission, Delivery Boundaries and the Final-Flush Race* (aicassindra.com). A scripted turn loop with a mailbox. Steers are accepted while admission is open and delivered at the boundary before the next step; tool calls planned before the steer are dropped. It reproduces the lost-message race when the final flush checks pending input before closing admission, and shows the atomic close that avoids it. Input after the turn closes waits for the next task.

## Prerequisites

- Python 3.11 or newer. Standard library only.
- `.env.example` documents that nothing secret is read from the environment. No API keys, no network calls beyond loopback.

## Sample input

A scripted plan (sample, tool:lookup_order, tool:draft_refund, sample, final) and steers about CASE-7031 and CASE-7032.

## Commands

From this directory:

```
python steering.py
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

A steer at step 1 drops both stale tool calls (executed: sample, sample, final). Check-then-close: the steer is lost. Atomic close: it is delivered in the same turn (sample, final, sample, final). After the final answer a steer is queued for the next task. 6 tests pass.

## Limitations

Interleavings are explicit, not threads. The scripted model is a list, not a provider call.

Views are my own and do not represent any employer, past or present.
