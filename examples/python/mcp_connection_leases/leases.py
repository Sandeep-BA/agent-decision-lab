"""Author: Sandeep Belgavi. One shared stdio-style MCP connection used by several chats.
In-process model: JSON-RPC message dicts, no subprocess, no model. The lease key is an
example vendor key; Codex CLI 0.167.0 uses its own extension name."""
import itertools

LEASE_KEY = "com.example.store/lease"


class StatefulServer:
    """A help-desk MCP server that remembers the 'selected case' per lease (or globally)."""
    def __init__(self, supports_leases):
        self.supports_leases = supports_leases
        self.selected = {}            # lease -> case id
        self.notes = []               # (case, text)
        self.pending = {}             # id -> (method, params)
        self.cancelled = set()
        self.released = set()

    def _scope(self, params):
        return params.get("_meta", {}).get(LEASE_KEY, "global") if self.supports_leases else "global"

    def receive(self, msg):
        if msg.get("method") == "notifications/cancelled":
            self.cancelled.add(msg["params"]["requestId"]); return None
        if msg.get("method") == "com.example.store/release":
            self.released.add(msg["params"]["lease"]); return None
        self.pending[msg["id"]] = msg
        return msg["id"]

    def complete(self, request_id):
        """Finish one pending request; returns the response or None if it was cancelled."""
        msg = self.pending.pop(request_id)
        if request_id in self.cancelled:
            return None
        args, scope = msg["params"]["arguments"], self._scope(msg["params"])
        if msg["params"]["name"] == "open_case":
            self.selected[scope] = args["case"]
            text = f"selected {args['case']}"
        else:
            case = self.selected.get(scope)
            self.notes.append((case, args["text"]))
            text = f"note added to {case}"
        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": text}]}}


class Host:
    """Owns the connection: unique request ids, host-assigned leases, response routing."""
    def __init__(self, server, use_leases=True, cancel_before_release=True, override_meta=True):
        self.server, self.use_leases, self.cancel_first, self.override = server, use_leases, cancel_before_release, override_meta
        self.ids = itertools.count(1)
        self.leases = {}
        self.owner = {}               # request id -> chat
        self.delivered = []           # (chat, text)
        self.dropped = []
        self.log = []

    def open(self, chat):
        if self.use_leases and self.server.supports_leases:
            self.leases[chat] = f"lease-{len(self.leases) + 1}"

    def call(self, chat, name, arguments, meta=None):
        params = {"name": name, "arguments": arguments, "_meta": dict(meta or {})}
        if chat in self.leases and (self.override or LEASE_KEY not in params["_meta"]):
            params["_meta"][LEASE_KEY] = self.leases[chat]       # host-owned value replaces any caller value
        rid = next(self.ids)
        self.owner[rid] = chat
        self.server.receive({"jsonrpc": "2.0", "id": rid, "method": "tools/call", "params": params})
        self.log.append(f"{chat} -> tools/call {name} id={rid} lease={params['_meta'].get(LEASE_KEY, 'none')}")
        return rid

    def release(self, chat):
        mine = [rid for rid, c in self.owner.items() if c == chat and rid in self.server.pending]
        if self.cancel_first:
            for rid in mine:
                self.server.receive({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": rid, "reason": "chat closed"}})
                self.log.append(f"{chat}: cancel id={rid} before release")
        lease = self.leases.pop(chat, None)
        if lease:
            self.server.receive({"jsonrpc": "2.0", "method": "com.example.store/release", "params": {"lease": lease}})
        for rid in mine:
            self.owner[rid] = None                                # responses for a closed chat are ignored
        self.log.append(f"{chat}: released {lease or 'no lease'}")

    def finish(self, rid):
        resp = self.server.complete(rid)
        chat = self.owner.get(rid)
        if resp is None:
            self.log.append(f"id={rid}: cancelled, no response"); return
        if chat is None:
            self.dropped.append(rid); self.log.append(f"id={rid}: response arrived after its chat closed; ignored"); return
        self.delivered.append((chat, resp["result"]["content"][0]["text"]))


def scenario(supports_leases=True, use_leases=True, cancel_before_release=True, spoof=False, override_meta=True):
    """Geetha's chat works CASE-4410, Jenya's chat works CASE-4415, over one connection."""
    server = StatefulServer(supports_leases)
    host = Host(server, use_leases, cancel_before_release, override_meta)
    for chat in ("chat-geetha", "chat-jenya"):
        host.open(chat)
    host.finish(host.call("chat-geetha", "open_case", {"case": "CASE-4410"}))
    host.finish(host.call("chat-jenya", "open_case", {"case": "CASE-4415"}))
    host.finish(host.call("chat-geetha", "add_note", {"text": "customer sent the return label"}))
    meta = {LEASE_KEY: host.leases.get("chat-geetha", "lease-1")} if spoof else None
    host.finish(host.call("chat-jenya", "add_note", {"text": "asked for a replacement copy"}, meta))
    slow = host.call("chat-geetha", "add_note", {"text": "refund approved"})
    host.release("chat-geetha")
    host.finish(slow)
    return server, host


if __name__ == "__main__":
    for kw in [dict(supports_leases=False), dict(), dict(spoof=True, override_meta=False), dict(spoof=True), dict(cancel_before_release=False)]:
        s, h = scenario(**kw)
        print(kw, "notes:", s.notes, "dropped:", h.dropped)
