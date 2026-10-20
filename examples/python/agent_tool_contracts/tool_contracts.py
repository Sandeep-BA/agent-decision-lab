"""Testing a service once an agent calls it: consumer contract, recorded model replay, effect invariants.

Author: Sandeep Belgavi. Companion to the aicassindra.com guide "Testing a Service Once an Agent
Calls It". Standard library only. No model provider is called: the "model" is a replay store of
recorded responses, and the property check uses a seeded generator with shrinking.

Commands (from the repository root):
  python examples/python/agent_tool_contracts/tool_contracts.py verify --provider v1
  python examples/python/agent_tool_contracts/tool_contracts.py verify --provider renamed
  python examples/python/agent_tool_contracts/tool_contracts.py verify --provider lenient
  python examples/python/agent_tool_contracts/tool_contracts.py invariants --handler buggy --seed 7
  python examples/python/agent_tool_contracts/tool_contracts.py invariants --handler fixed --seed 7
  python examples/python/agent_tool_contracts/tool_contracts.py replay
"""
import argparse
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "fixtures" / "refund_contract.json"
REPLAYS = HERE / "fixtures" / "recorded_model_responses.json"
CAPTURED = {"o-1": 100, "o-2": 60}


class RefundService:
    """The provider. Variants reproduce the three changes discussed in the guide.

    variant="v1"       the reference implementation
    variant="renamed"  renames remaining_refundable to refundable_balance (a tidy-up)
    variant="lenient"  accepts negative amounts as reversals
    check_cap=False    the buggy handler: no cumulative cap check against the captured amount
    """

    def __init__(self, variant="v1", check_cap=True):
        self.variant = variant
        self.check_cap = check_cap
        self.captured = dict(CAPTURED)
        self.refunds = []            # (order_id, amount, key)
        self.by_key = {}

    def refunded(self, order_id):
        return sum(a for o, a, _ in self.refunds if o == order_id)

    def refund_order(self, order_id, amount, reason, idempotency_key):
        if idempotency_key in self.by_key:                     # retried call: same answer, no new effect
            return self.by_key[idempotency_key]
        if order_id not in self.captured:
            return {"error": "unknown order"}
        if amount < 1 and self.variant != "lenient":
            return {"error": "amount must be positive"}
        remaining = self.captured[order_id] - self.refunded(order_id)
        if self.check_cap and amount > remaining:
            return {"error": "amount exceeds refundable balance", "remaining_refundable": remaining}
        self.refunds.append((order_id, amount, idempotency_key))
        result = {"refund_id": "rf-%d" % len(self.refunds), "amount": amount}
        balance = self.captured[order_id] - self.refunded(order_id)
        result["refundable_balance" if self.variant == "renamed" else "remaining_refundable"] = balance
        self.by_key[idempotency_key] = result
        return result


# ---------------------------------------------------------------- consumer contract

def check_interaction(schema, call, provider):
    """Replay one recorded agent call against the real provider; return the problems found."""
    problems = []
    for field in schema["required"]:
        if field not in call["arguments"]:
            problems.append("missing required argument " + field)
    result = provider(call["arguments"])
    for field in call["fields_read_next"]:
        if field not in result:
            problems.append("result no longer carries " + field)
    if call.get("expect_error") and "error" not in result:
        problems.append("call that used to be rejected is now accepted")
    return problems


def verify(contract, variant="v1"):
    """Provider verification: every interaction runs against a fresh service, in recorded order."""
    service = RefundService(variant)
    failures = {}
    for call in contract["interactions"]:
        found = check_interaction(contract["tool"]["inputSchema"], call, lambda args: service.refund_order(**args))
        if found:
            failures[call["id"]] = found
    return failures


# ---------------------------------------------------------------- recorded model replay

class ReplayMiss(Exception):
    """A model request that was never recorded. Replay tests must fail, never call a live model."""


def request_hash(model, messages):
    canonical = json.dumps({"model": model, "messages": messages}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class ReplayModel:
    def __init__(self, store):
        self.store = store

    def complete(self, model, messages):
        key = request_hash(model, messages)
        if key not in self.store:
            raise ReplayMiss("no recorded response for request %s" % key)
        return self.store[key]


def run_turn(model_client, service, user_text, model="staging-model-2026-10"):
    """A tiny agent runtime: one model call proposes a tool call, the runtime executes it, a second
    model call writes the answer. Every branch here is deterministic once responses are fixed."""
    messages = [{"role": "user", "content": user_text}]
    first = model_client.complete(model, messages)
    call = first["tool_call"]
    if call["name"] != "refund_order":
        raise ValueError("unexpected tool " + call["name"])
    result = service.refund_order(**call["arguments"])
    messages += [{"role": "assistant", "tool_call": call}, {"role": "tool", "content": result}]
    second = model_client.complete(model, messages)
    return {"tool_result": result, "answer": second["text"]}


def record_fixture():
    """Builds the synthetic replay store (what a staging recording job would have written)."""
    model = "staging-model-2026-10"
    user = "My order o-1 arrived a week late, can I get 40 back?"
    call = {"name": "refund_order", "arguments": {"order_id": "o-1", "amount": 40, "reason": "late delivery", "idempotency_key": "o-1:conv-7"}}
    m1 = [{"role": "user", "content": user}]
    result = RefundService().refund_order(**call["arguments"])
    m2 = m1 + [{"role": "assistant", "tool_call": call}, {"role": "tool", "content": result}]
    return {request_hash(model, m1): {"tool_call": call},
            request_hash(model, m2): {"text": "Refunded 40. You can still claim up to 60 on this order."}}


# ---------------------------------------------------------------- effect invariants

def generate_calls(rng, size):
    """Agent-like call sequences: retries with the same key and re-plans with a fresh key."""
    calls = []
    for _ in range(size):
        order = rng.choice(["o-1", "o-2"])
        amount = rng.choice([10, 25, 40, 55, 70])
        key = "%s:%s" % (order, rng.choice(["k1", "k2", "k3"]))
        calls.append({"order_id": order, "amount": amount, "reason": rng.choice(["late", "late delivery", "damaged"]), "idempotency_key": key})
    return calls


def violates(calls, check_cap):
    service = RefundService(check_cap=check_cap)
    for c in calls:
        service.refund_order(**c)
    return [o for o, cap in service.captured.items() if service.refunded(o) > cap]


def shrink(calls, check_cap):
    """Remove calls one at a time while the failure persists, like Hypothesis shrinking does."""
    changed = True
    while changed:
        changed = False
        for i in range(len(calls)):
            candidate = calls[:i] + calls[i + 1:]
            if violates(candidate, check_cap):
                calls, changed = candidate, True
                break
    return calls


def check_invariants(check_cap, seed=7, examples=200, max_size=12):
    rng = random.Random(seed)
    for n in range(examples):
        calls = generate_calls(rng, rng.randint(0, max_size))
        if violates(calls, check_cap):
            return {"failed_after": n + 1, "minimal": shrink(calls, check_cap)}
    return {"failed_after": None, "examples": examples}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--provider", choices=["v1", "renamed", "lenient"], default="v1")
    inv = sub.add_parser("invariants")
    inv.add_argument("--handler", choices=["buggy", "fixed"], default="fixed")
    inv.add_argument("--seed", type=int, default=7)
    sub.add_parser("replay")
    args = ap.parse_args()
    if args.cmd == "verify":
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        failures = verify(contract, args.provider)
        print("provider=%s interactions=%d failures=%d" % (args.provider, len(contract["interactions"]), len(failures)))
        for cid, problems in failures.items():
            print("  %s: %s" % (cid, "; ".join(problems)))
    elif args.cmd == "invariants":
        out = check_invariants(args.handler == "fixed", args.seed)
        if out["failed_after"] is None:
            print("handler=%s invariant held for %d generated sequences" % (args.handler, out["examples"]))
        else:
            print("handler=%s invariant violated after %d sequences; minimal sequence (%d calls):" % (args.handler, out["failed_after"], len(out["minimal"])))
            for c in out["minimal"]:
                print("  refund_order(%s, %d, key=%s)" % (c["order_id"], c["amount"], c["idempotency_key"]))
    else:
        store = json.loads(REPLAYS.read_text(encoding="utf-8"))
        out = run_turn(ReplayModel(store), RefundService(), "My order o-1 arrived a week late, can I get 40 back?")
        print("replayed turn: tool_result=%s" % json.dumps(out["tool_result"], sort_keys=True))
        print("answer: %s" % out["answer"])


if __name__ == "__main__":
    main()
