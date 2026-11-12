"""Author: Sandeep Belgavi. Accumulating a streamed model turn when the client retries mid-stream.
Synthetic event list; no provider is called. Event kinds: text, tool_call, retry, finish."""

ATTEMPT_1 = [("text", "Checking order ORD-7781. "), ("tool_call", {"id": "c1", "name": "issue_refund", "args": {"order": "ORD-7781", "amount": 49900}}),
             ("text", "Refunding the dam")]
ATTEMPT_2 = [("text", "Checking order ORD-7781. "), ("text", "The book arrived damaged, so "),
             ("tool_call", {"id": "c7", "name": "issue_refund", "args": {"order": "ORD-7781", "amount": 49900}}),
             ("text", "I have started a full refund."), ("finish", "stop")]
STREAM = ATTEMPT_1 + [("retry", "connection reset after 3 events")] + ATTEMPT_2


def accumulate(events, policy):
    """policy: 'naive' keeps everything; 'reset' discards the abandoned attempt on retry;
    'reset-late-exec' also refuses to run tools before the attempt finishes."""
    text, calls, executed, attempt = [], [], [], 1
    shown = []                                # what a UI rendering deltas would have shown
    for kind, value in events:
        if kind == "retry":
            if policy != "naive":
                text, calls = [], []
                shown.append("[reset]")
            attempt += 1
        elif kind == "text":
            text.append(value); shown.append(value)
        elif kind == "tool_call":
            calls.append(dict(value, attempt=attempt))
            if policy == "naive" or policy == "reset":
                executed.append(dict(value, attempt=attempt))     # runs as soon as it streams
        elif kind == "finish":
            if policy == "reset-late-exec":
                executed.extend(calls)
    return {"text": "".join(text), "calls": calls, "executed": executed, "attempts": attempt, "shown": shown}


if __name__ == "__main__":
    for p in ("naive", "reset", "reset-late-exec"):
        r = accumulate(STREAM, p)
        print(p, "| refunds executed:", len(r["executed"]), "| text:", r["text"])


def effect_keys(executed, turn_id="turn-12"):
    """Idempotency keys from the turn and the call content; provider call ids differ per attempt."""
    import hashlib, json
    return {hashlib.sha256(json.dumps([turn_id, c["name"], c["args"]], sort_keys=True).encode()).hexdigest()[:16] for c in executed}
