"""Rules first, agent for the residual: an invoice exception router.

Author: Sandeep Belgavi. Companion to "Rules First, Agent for the Residual" (aicassindra.com).

An accounts-payable pipeline already matches invoices against purchase orders and goods receipts with
deterministic rules. This example adds an agent only for the invoices the rules cannot decide, and keeps
three things deterministic around it:

* the router, which sends an invoice to the agent only when no rule decided it;
* the validator, which refuses any agent action that breaks a hard constraint;
* the acceptance policy, which takes an agent decision only above a confidence threshold and otherwise
  queues the invoice for a person.

``StubAgent`` stands in for a model. Its behaviour per exception type is fixed in a table so that the
arithmetic can be checked; its numbers describe the stub, not any real model.
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass

ACTIONS = {"approve", "reject", "request_credit_note", "escalate"}
APPROVAL_LIMIT = 5000.0       # an agent may never approve above this amount
PRICE_TOLERANCE = 0.02        # the existing rule: approve if the price variance is within 2 percent


@dataclass(frozen=True)
class Invoice:
    id: str
    kind: str          # fixture category, used only to generate data and score results
    amount: float
    po_amount: float | None
    received_qty: int
    invoiced_qty: int
    duplicate: bool
    truth: str         # the action a reviewer agreed is correct


def fixture(n: int = 1000, seed: int = 7) -> list[Invoice]:
    """Synthetic invoices. Shares per category are fixed; amounts vary with a seeded generator."""
    rng = random.Random(seed)
    plan = [("exact", 700), ("duplicate", 40), ("small_variance", 90), ("large_variance", 60),
            ("short_shipment", 50), ("missing_po", 30), ("freight_line", 30)]
    assert sum(k for _, k in plan) == n
    out = []
    for kind, count in plan:
        for _ in range(count):
            po = round(rng.uniform(200, 9000), 2)
            amount, recv, inv, truth = po, 10, 10, "approve"
            if kind == "duplicate":
                truth = "reject"
            elif kind == "small_variance":
                amount = round(po * (1 + rng.uniform(-0.019, 0.019)), 2)
            elif kind == "large_variance":
                amount = round(po * (1 + rng.uniform(0.03, 0.12)), 2)
                truth = "request_credit_note"
            elif kind == "short_shipment":
                recv = rng.randint(6, 9)
                truth = "request_credit_note"
            elif kind == "missing_po":
                truth = "escalate"
            elif kind == "freight_line":
                amount = round(po + rng.uniform(15, 60), 2)
            out.append(Invoice(f"INV-{len(out) + 1:04d}", kind, amount, None if kind == "missing_po" else po,
                               recv, inv, kind == "duplicate", truth))
    return out


def rules(inv: Invoice, freight_rule: bool = False) -> str | None:
    """The existing deterministic pipeline. Returns an action, or None when it cannot decide."""
    if inv.duplicate:
        return "reject"
    if inv.po_amount is None or inv.received_qty != inv.invoiced_qty:
        return None
    variance = (inv.amount - inv.po_amount) / inv.po_amount
    if abs(variance) <= PRICE_TOLERANCE:
        return "approve"
    if freight_rule and 0 < inv.amount - inv.po_amount <= 60:
        return "approve"     # a rule promoted from repeated agent decisions
    return None


# The stub's behaviour per exception type: (share answered correctly, confidence when correct,
# confidence when wrong, wrong action). Fixed so that every figure in the README can be recomputed.
STUB_PROFILE = {
    "large_variance": (0.90, 0.86, 0.62, "approve"),
    "short_shipment": (0.80, 0.81, 0.74, "approve"),
    "missing_po": (0.50, 0.55, 0.58, "approve"),
    "freight_line": (0.95, 0.92, 0.70, "request_credit_note"),
}


class StubAgent:
    """Deterministic stand-in for a model: every n-th invoice of a kind is answered wrongly."""

    def __init__(self):
        self.seen: dict[str, int] = {}

    def decide(self, inv: Invoice) -> tuple[str, float]:
        share, conf_ok, conf_bad, wrong = STUB_PROFILE[inv.kind]
        i = self.seen.get(inv.kind, 0)
        self.seen[inv.kind] = i + 1
        correct = (i % 20) < round(share * 20)
        return (inv.truth, conf_ok) if correct else (wrong, conf_bad)


def validate(inv: Invoice, action: str) -> str | None:
    """Hard constraints the agent cannot override. Returns a reason when the action is refused."""
    if action not in ACTIONS:
        return "unknown action"
    if action == "approve" and inv.po_amount is None:
        return "approval without a purchase order"
    if action == "approve" and inv.amount > APPROVAL_LIMIT:
        return "approval above the agent limit"
    if action == "approve" and inv.received_qty < inv.invoiced_qty:
        return "approval of goods not received"
    return None


def run(threshold: float = 0.8, freight_rule: bool = False, invoices: list[Invoice] | None = None) -> dict:
    invoices = invoices if invoices is not None else fixture()
    agent = StubAgent()
    counts = dict(rules=0, agent_accepted=0, agent_wrong_accepted=0, validator_refused=0,
                  below_threshold=0, human_queue=0, rules_wrong=0, agent_calls=0, validator_reasons={})
    for inv in invoices:
        action = rules(inv, freight_rule)
        if action is not None:
            counts["rules"] += 1
            counts["rules_wrong"] += action != inv.truth
            continue
        counts["agent_calls"] += 1
        proposed, confidence = agent.decide(inv)
        reason = validate(inv, proposed)
        if reason:
            counts["validator_refused"] += 1
            counts["validator_reasons"][reason] = counts["validator_reasons"].get(reason, 0) + 1
            counts["human_queue"] += 1
        elif proposed == "escalate" or confidence < threshold:
            counts["below_threshold"] += proposed != "escalate"
            counts["human_queue"] += 1
        else:
            counts["agent_accepted"] += 1
            counts["agent_wrong_accepted"] += proposed != inv.truth
    n = len(invoices)
    counts["automated_pct"] = round(100 * (counts["rules"] + counts["agent_accepted"]) / n, 1)
    counts["residual_pct"] = round(100 * counts["agent_calls"] / n, 1)
    accepted = counts["agent_accepted"]
    counts["agent_error_pct_of_accepted"] = round(100 * counts["agent_wrong_accepted"] / accepted, 1) if accepted else 0.0
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description="Rules first, agent for the residual.")
    ap.add_argument("--threshold", type=float, default=0.8)
    ap.add_argument("--freight-rule", action="store_true", help="promote the freight-line pattern to a rule")
    args = ap.parse_args()
    print(json.dumps(run(args.threshold, args.freight_rule), indent=2))


if __name__ == "__main__":
    main()
