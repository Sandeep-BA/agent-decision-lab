"""Tool-selection regression test: fixed cases, versioned tool descriptions, per-case diffs.

Author: Sandeep Belgavi. Companion to "Tool Descriptions Are Prompts" (aicassindra.com).
Synthetic Belgavi's Book Store help-desk messages.

Two modes:
  python selection.py report              offline: summarise the recorded runs in recorded/ (no model needed)
  python selection.py live MODEL REPEATS  live: call a local Ollama server at 127.0.0.1:11434 and print JSON
The recorded runs were made on 3 November 2026 with Ollama 0.40.12 on one Windows 11 machine.
"""
import collections
import glob
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SYSTEM = "You are the help desk of Belgavi's Book Store. Call exactly one tool."
OID = {"order_id": {"type": "string", "description": "Order number such as BK-1042"}}
BASE = {
    "lookup_order": "Look up an order: items, status, shipping and delivery dates.",
    "start_return": "Start a return for a delivered order. Creates a return label.",
    "issue_refund": "Refund money for an order that was returned or never delivered.",
    "check_stock": "Check whether a book is in stock, by title or ISBN.",
}
VERSIONS = {
    "v1": BASE,
    "v2": dict(BASE, start_return=BASE["start_return"] + " Use this for anything about getting money back."),
    "v3": dict(BASE, start_return="Start a return or a refund for an order. Creates a return label when needed.",
               issue_refund="Refund an order that was never delivered."),
}
CASES = [
    ("Where is my order BK-1042?", "lookup_order"),
    ("When will BK-1043 arrive?", "lookup_order"),
    ("Has order BK-1050 shipped yet?", "lookup_order"),
    ("What books are in order BK-1051?", "lookup_order"),
    ("I want to send back the book from BK-1044, it arrived damaged.", "start_return"),
    ("Please give me a return label for BK-1045, wrong edition.", "start_return"),
    ("The cover of the novel in BK-1052 is torn, I want to return it.", "start_return"),
    ("Can I return BK-1053? I bought it twice by mistake.", "start_return"),
    ("BK-1046 never arrived, I want my money back.", "issue_refund"),
    ("I already mailed back BK-1047 last week, where is my refund?", "issue_refund"),
    ("Refund BK-1054 please, the parcel was lost.", "issue_refund"),
    ("You charged me twice for BK-1055, please refund one charge.", "issue_refund"),
    ("Do you have The Hobbit in stock?", "check_stock"),
    ("Is ISBN 9780140449136 available?", "check_stock"),
    ("Can I buy a copy of Dune today?", "check_stock"),
    ("Do you still have the atlas Jenya ordered last month on the shelf?", "check_stock"),
]


def tools_for(descs):
    def tool(name, props, required):
        return {"type": "function", "function": {"name": name, "description": descs[name],
                "parameters": {"type": "object", "properties": props, "required": required}}}
    return [tool("lookup_order", OID, ["order_id"]),
            tool("start_return", dict(OID, reason={"type": "string"}), ["order_id", "reason"]),
            tool("issue_refund", dict(OID, amount={"type": "number"}), ["order_id"]),
            tool("check_stock", {"query": {"type": "string"}}, ["query"])]


def first_tool(model, tools, text, url="http://127.0.0.1:11434/api/chat"):
    body = {"model": model, "stream": False, "tools": tools, "options": {"temperature": 0, "seed": 7},
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]}
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        reply = json.load(r)["message"]
    calls = reply.get("tool_calls") or []
    return calls[0]["function"]["name"] if calls else None


def load_recorded():
    """{(model, version): {case_text: [tool per repeat]}} from every file in recorded/."""
    runs = collections.defaultdict(lambda: collections.defaultdict(list))
    for path in sorted(glob.glob(os.path.join(HERE, "recorded", "*.json"))):
        data = json.load(open(path, encoding="utf-8"))
        for r in data["results"]:
            runs[(data["model"], r["version"])][r["text"]].append(r["got"])
    return runs


def majority(tools):
    return collections.Counter(tools).most_common(1)[0][0]


def score(run):
    expected = dict(CASES)
    return sum(t == expected[text] for text, tools in run.items() for t in tools)


def diff(baseline, candidate):
    """Per-case changes of the majority tool: {text: (old, new)}."""
    return {t: (majority(baseline[t]), majority(candidate[t]))
            for t in baseline if majority(baseline[t]) != majority(candidate[t])}


def new_failures(baseline, candidate):
    expected = dict(CASES)
    return sorted(t for t, (old, new) in diff(baseline, candidate).items()
                  if old == expected[t] and new != expected[t])


def report():
    runs = load_recorded()
    for model in sorted({m for m, _ in runs}):
        base = runs[(model, "v1")]
        for version in ("v1", "v2", "v3"):
            run = runs.get((model, version))
            if not run:
                continue
            n = sum(len(v) for v in run.values())
            print("%-22s %s correct %2d/%d new failures vs v1: %s" % (
                model, version, score(run), n, new_failures(base, run) if version != "v1" else "-"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "live":
        model, repeats = sys.argv[2], int(sys.argv[3])
        out = [{"version": v, "text": t, "expected": e, "got": first_tool(model, tools_for(d), t), "repeat": k}
               for v, d in VERSIONS.items() for t, e in CASES for k in range(repeats)]
        print(json.dumps({"model": model, "repeats": repeats, "versions": VERSIONS, "results": out}, indent=1))
    else:
        report()
