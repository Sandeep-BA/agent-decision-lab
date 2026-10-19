"""Durable execution by history replay, in miniature.

Author: Sandeep Belgavi. Teaching model with synthetic data; no model provider is called.

Workflow code is deterministic and only branches on activity results. Activities (the model
call, placing the order, notifying) run through the Replayer, which returns recorded results
on replay and executes only what history does not contain. A patch marker versions code
changes while runs are in flight.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

FIXTURE = Path(__file__).with_name("fixtures") / "history_p204.json"


class NonDeterministic(Exception):
    """The code issued a command that does not match the recorded history."""


@dataclass
class Replayer:
    """Minimal engine: a history of (kind, name, result) entries and a live executor."""
    run_id: str
    history: list[dict]
    execute: callable
    signals: dict = field(default_factory=dict)
    pos: int = 0
    live_activities: int = 0

    def _next(self, kind: str, name: str):
        """Return the recorded entry at this position if it matches, None if history is exhausted."""
        if self.pos < len(self.history):
            entry = self.history[self.pos]
            if (entry["kind"], entry["name"]) != (kind, name):
                raise NonDeterministic(
                    f"history has {entry['kind']} {entry['name']} at step {self.pos}; code issued {kind} {name}")
            self.pos += 1
            return entry
        return None

    def activity(self, name: str, *args):
        entry = self._next("activity", name)
        if entry is not None:
            return entry["result"]                      # replay: nothing runs
        result = self.execute(self.run_id, name, *args)  # live: run once and record
        self.history.append({"kind": "activity", "name": name, "result": result})
        self.pos += 1
        self.live_activities += 1
        return result

    def patched(self, patch_id: str) -> bool:
        """True on new runs (records the patch); False on histories that predate it."""
        if self.pos < len(self.history):
            entry = self.history[self.pos]
            if entry["kind"] == "patch" and entry["name"] == patch_id:
                self.pos += 1
                return True
            return False                               # old history: take the old path, consume nothing
        self.history.append({"kind": "patch", "name": patch_id})
        self.pos += 1
        return True

    def wait_signal(self, name: str):
        """Blocked waits are recorded too, like the workflow task that evaluated them, so that a
        later code change behind the wait is replayed as 'old history' rather than run live."""
        while self.pos < len(self.history):
            entry = self.history[self.pos]
            if entry["kind"] == "blocked" and entry["name"] == name:
                self.pos += 1                           # the recorded wait; keep looking for the signal
                continue
            if entry["kind"] == "signal" and entry["name"] == name:
                self.pos += 1
                return entry["result"]
            raise NonDeterministic(
                f"history has {entry['kind']} {entry['name']} at step {self.pos}; code waited for signal {name}")
        if name not in self.signals:
            if not (self.history and self.history[-1] == {"kind": "blocked", "name": name}):
                self.history.append({"kind": "blocked", "name": name})
            raise Waiting(name)
        value = self.signals[name]
        self.history.append({"kind": "signal", "name": name, "result": value})
        self.pos += 1
        return value


class Waiting(Exception):
    """The workflow is blocked on a signal that has not arrived."""


# ---- activities: everything non-deterministic lives here -------------------------------
MODEL_CALLS = 0


def execute_activity(run_id: str, name: str, *args):
    global MODEL_CALLS
    if name == "draft_order":
        MODEL_CALLS += 1                                # stands in for a provider call
        (request,) = args
        return {"supplier": "B", "amount": request["budget"] - 800, "rationale": "synthetic"}
    if name == "compliance_check":
        return {"ok": True}
    if name == "place_order":
        (proposal,) = args
        # an effecting activity carries the workflow id as its idempotency key
        return {"order_id": f"ORD-{proposal['amount']}-{proposal['supplier']}", "idempotency_key": f"{run_id}:place_order"}
    if name == "notify":
        return {"sent": True}
    raise KeyError(name)


# ---- workflow code: deterministic, branches only on activity results -------------------
def procurement_v1(wf: Replayer, request: dict):
    proposal = wf.activity("draft_order", request)
    if proposal["amount"] > 5000:
        if not wf.wait_signal("approval"):
            return "rejected"
    order = wf.activity("place_order", proposal)
    wf.activity("notify", order["order_id"])
    return order["order_id"]


def procurement_v2(wf: Replayer, request: dict):
    proposal = wf.activity("draft_order", request)
    if wf.patched("compliance-check-2026-10"):
        wf.activity("compliance_check", proposal)
    if proposal["amount"] > 5000:
        if not wf.wait_signal("approval"):
            return "rejected"
    order = wf.activity("place_order", proposal)
    wf.activity("notify", order["order_id"])
    return order["order_id"]


def procurement_reordered(wf: Replayer, request: dict):
    """An unversioned change: notify before placing the order. Breaks replay of old histories."""
    proposal = wf.activity("draft_order", request)
    wf.activity("notify", "early")
    order = wf.activity("place_order", proposal)
    return order["order_id"]


def resume(run_id: str, history: list[dict], workflow, request: dict, signals: dict | None = None) -> tuple[str, Replayer]:
    wf = Replayer(run_id=run_id, history=list(history), execute=execute_activity, signals=signals or {})
    result = workflow(wf, request)
    return result, wf


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if not a.demo:
        ap.print_help()
        return
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    global MODEL_CALLS
    MODEL_CALLS = 0
    print(f"replay {fixture['run_id']} from {len(fixture['history'])} recorded entries, approval=granted")
    result, wf = resume(fixture["run_id"], fixture["history"], procurement_v2, fixture["request"], {"approval": True})
    names = [e["name"] for e in wf.history]
    print("  draft_order: replayed (model not called)")
    print("  compliance_check: " + ("executed" if "compliance_check" in names else "skipped (patch compliance-check-2026-10 absent from this history)"))
    print("  place_order: executed live with idempotency key " + next(e["result"]["idempotency_key"] for e in wf.history if e["name"] == "place_order"))
    print("  notify: executed live")
    print(f"result={result} live_activities={wf.live_activities} model_calls={MODEL_CALLS}")
    _result2, wf2 = resume("P-205", [], procurement_v2, fixture["request"], {"approval": True})
    kinds = [(e["kind"], e["name"]) for e in wf2.history]
    print("new run P-205 on the same code: patch recorded, compliance_check executed"
          if ("patch", "compliance-check-2026-10") in kinds and ("activity", "compliance_check") in kinds else "new run P-205: unexpected history")


if __name__ == "__main__":
    main()
