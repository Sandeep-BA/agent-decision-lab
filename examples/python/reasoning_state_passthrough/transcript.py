"""Keep provider reasoning state intact through a provider-neutral transcript store.

Author: Sandeep Belgavi. Standard library only. No provider is called: the responses below are synthetic
fixtures shaped after the documented formats (Anthropic thinking and redacted_thinking blocks, OpenAI
Responses reasoning items with encrypted_content, Gemini generateContent parts with thoughtSignature).
The checks implement the documented round-trip rules locally; they are not the providers' own validation.
"""
import copy
import json

ANTHROPIC_RESPONSE = {"role": "assistant", "content": [
    {"type": "thinking", "thinking": "", "signature": "sig-A1"},
    {"type": "redacted_thinking", "data": "enc-R1"},
    {"type": "tool_use", "id": "tu_1", "name": "get_order", "input": {"order_id": "O-88213"}}]}

OPENAI_OUTPUT = [
    {"type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "enc-O1"},
    {"type": "function_call", "call_id": "call_1", "name": "get_order", "arguments": "{\"order_id\": \"O-88213\"}"}]

GEMINI_RESPONSE = {"role": "model", "parts": [
    {"functionCall": {"name": "get_order", "args": {"order_id": "O-88213"}}, "thoughtSignature": "sig-G1"},
    {"text": "Checking the order."}]}

TOOL_RESULT = {"order_id": "O-88213", "charges": 2, "status": "paid"}


class Store:
    """A transcript store. `keep_native` decides whether the provider payload survives persistence."""
    def __init__(self, keep_native):
        self.keep_native, self.turns = keep_native, []

    def save(self, provider, family, payload):
        neutral = to_neutral(provider, payload)
        if self.keep_native:
            neutral["native"] = {"provider": provider, "family": family, "payload": json.dumps(payload)}
        self.turns.append(json.loads(json.dumps(neutral)))   # simulate a round trip through a database

    def replay(self, provider, family):
        """Rebuild the assistant turn for the next request to `provider` / `family`."""
        turn = self.turns[-1]
        native = turn.get("native")
        if native and native["provider"] == provider and native["family"] == family:
            return json.loads(native["payload"])
        return from_neutral(provider, turn)


def to_neutral(provider, payload):
    calls, text = [], []
    if provider == "anthropic":
        for b in payload["content"]:
            if b["type"] == "tool_use":
                calls.append({"id": b["id"], "name": b["name"], "args": b["input"]})
            elif b["type"] == "text":
                text.append(b["text"])
    elif provider == "openai":
        for item in payload:
            if item["type"] == "function_call":
                calls.append({"id": item["call_id"], "name": item["name"], "args": json.loads(item["arguments"])})
    elif provider == "gemini":
        for part in payload["parts"]:
            if "functionCall" in part:
                fc = part["functionCall"]
                calls.append({"id": fc["name"], "name": fc["name"], "args": fc["args"]})
            elif "text" in part:
                text.append(part["text"])
    return {"role": "assistant", "text": " ".join(text), "tool_calls": calls}


def from_neutral(provider, turn):
    """What a lossy adapter sends back: tool calls and text, no reasoning state."""
    if provider == "anthropic":
        return {"role": "assistant", "content": [{"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["args"]}
                                                 for c in turn["tool_calls"]]}
    if provider == "openai":
        return [{"type": "function_call", "call_id": c["id"], "name": c["name"], "arguments": json.dumps(c["args"])}
                for c in turn["tool_calls"]]
    parts = [{"functionCall": {"name": c["name"], "args": c["args"]}} for c in turn["tool_calls"]]
    if turn["text"]:
        parts.append({"text": turn["text"]})
    return {"role": "model", "parts": parts}


def check(provider, original, replayed):
    """Return a list of rule violations for sending `replayed` back where `original` was received."""
    problems = []
    if provider == "anthropic":
        want = [b for b in original["content"] if b["type"] in ("thinking", "redacted_thinking")]
        got = [b for b in replayed["content"] if b["type"] in ("thinking", "redacted_thinking")]
        if got != want:
            problems.append("thinking and redacted_thinking blocks must come back complete, unmodified and in order")
    elif provider == "openai":
        want = [i for i in original if i["type"] == "reasoning"]
        got = [i for i in replayed if i["type"] == "reasoning"]
        if got != want:
            problems.append("reasoning items since the last user message must be passed back with encrypted_content")
    elif provider == "gemini":
        want = [p for p in original["parts"] if "thoughtSignature" in p]
        got = [p for p in replayed["parts"] if "thoughtSignature" in p]
        if got != want:
            problems.append("parts carrying thoughtSignature must be returned unchanged and unmerged")
    return problems


def only_thinking_filter(anthropic_response):
    """A common bug: keep blocks of type 'thinking' and 'tool_use' only, silently dropping redacted_thinking."""
    out = copy.deepcopy(anthropic_response)
    out["content"] = [b for b in out["content"] if b["type"] in ("thinking", "tool_use")]
    return out


def merge_gemini_text(gemini_response):
    """Another bug: merge all parts into one, which moves the signature off its original part."""
    parts = gemini_response["parts"]
    merged = {"text": " ".join(p.get("text", "") for p in parts).strip()}
    merged.update({k: v for p in parts for k, v in p.items() if k != "text"})
    return {"role": "model", "parts": [merged]}


def main():
    cases = [("anthropic", "claude-family-a", ANTHROPIC_RESPONSE), ("openai", "gpt-family-a", OPENAI_OUTPUT),
             ("gemini", "gemini-family-a", GEMINI_RESPONSE)]
    for keep in (False, True):
        for provider, family, response in cases:
            store = Store(keep_native=keep)
            store.save(provider, family, response)
            replayed = store.replay(provider, family)
            print(json.dumps({"keep_native": keep, "provider": provider, "violations": check(provider, response, replayed)}))


if __name__ == "__main__":
    main()
