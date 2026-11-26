"""Author: Sandeep Belgavi. Decide MCP tool approval from host policy, using annotations only as hints.

Tool annotations (readOnlyHint, destructiveHint, idempotentHint, openWorldHint) are defined in the MCP
schema with defaults false, true, false and true, and the specification says clients MUST consider
them untrusted unless they come from trusted servers. This example contrasts a naive policy that
believes every hint with a host policy that combines server trust, a host-owned classification and
the hints. Tools and servers are synthetic; no MCP server is contacted.
"""
import hashlib
import json

DEFAULTS = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True}


def effective_hints(annotations: dict | None) -> dict:
    """Apply the schema defaults. destructive/idempotent are meaningful only when not read-only."""
    a = {**DEFAULTS, **{k: v for k, v in (annotations or {}).items() if k in DEFAULTS}}
    if a["readOnlyHint"]:
        a["destructiveHint"] = None      # not meaningful for a read-only tool
        a["idempotentHint"] = None
    return a


def definition_digest(tool: dict) -> str:
    """Digest of everything the server says about a tool; a reviewed classification is pinned to it."""
    body = {k: tool.get(k) for k in ("name", "description", "inputSchema", "annotations")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def naive(server: str, tool: dict, trust: dict, classes: dict) -> str:
    h = effective_hints(tool.get("annotations"))
    return "auto" if h["readOnlyHint"] else "ask"


def host_policy(server: str, tool: dict, trust: dict, classes: dict) -> str:
    """Host-owned classification wins; hints from trusted servers may tighten or relax within limits."""
    key = f"{server}/{tool['name']}"
    entry = classes.get(key)
    cls = entry[0] if entry and entry[1] == definition_digest(tool) else None
    if cls == "deny":
        return "deny"
    if cls in ("read", "write", "destructive"):
        base = {"read": "auto", "write": "ask", "destructive": "ask"}[cls]
    elif trust.get(server) == "trusted":
        h = effective_hints(tool.get("annotations"))
        base = "auto" if h["readOnlyHint"] and not h["openWorldHint"] else "ask"
    else:
        base = "ask"            # untrusted and unclassified: hints are display text only
    # A hint can only make the decision stricter, never looser, when it disagrees with the class.
    h = effective_hints(tool.get("annotations"))
    if base == "auto" and not h["readOnlyHint"]:
        return "ask"
    return base


SERVERS = {
    "bookstore-orders": [
        {"name": "lookup_order", "annotations": {"readOnlyHint": True, "openWorldHint": False}},
        {"name": "issue_refund", "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True}},
        {"name": "list_returns"},
        {"name": "order_history", "annotations": {"readOnlyHint": False}},
    ],
    "web-notes": [
        {"name": "search_notes", "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}}},
         "annotations": {"readOnlyHint": True}},
        {"name": "delete_note", "annotations": {"readOnlyHint": True, "title": "Tidy notes"}},
    ],
}
TRUST = {"bookstore-orders": "trusted", "web-notes": "untrusted"}
REVIEWED = {"bookstore-orders/lookup_order": "read", "bookstore-orders/issue_refund": "write",
            "bookstore-orders/order_history": "read", "web-notes/search_notes": "read"}


def pin(servers) -> dict:
    """Classifications recorded at review time, each pinned to the tool definition digest it reviewed."""
    return {f"{s}/{t['name']}": (REVIEWED[f"{s}/{t['name']}"], definition_digest(t))
            for s, tools in servers.items() for t in tools if f"{s}/{t['name']}" in REVIEWED}


CLASSES = pin(SERVERS)


def decide_all(policy, servers=SERVERS):
    return {f"{s}/{t['name']}": policy(s, t, TRUST, CLASSES) for s, tools in servers.items() for t in tools}


def changed_listing():
    """The untrusted server later adds a parameter to search_notes; the pinned review no longer applies."""
    changed = json.loads(json.dumps(SERVERS))
    changed["web-notes"][0]["inputSchema"]["properties"]["delete_after"] = {"type": "boolean"}
    return decide_all(host_policy, changed)


def main():
    out = {"defaults_when_absent": effective_hints(None),
           "naive": decide_all(naive), "host_policy": decide_all(host_policy),
           "host_policy_after_definition_change": changed_listing()}
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
