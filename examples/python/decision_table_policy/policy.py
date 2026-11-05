"""Business rules in a versioned decision table: FIRST and UNIQUE hit policies, gap, overlap, reachability and
version-diff checks. Author: Sandeep Belgavi. Original example for the aicassindra.com article "Keep Business
Rules in a Decision Table the Agent Calls, Not in the Prompt". Standard library only.
Run: python policy.py fixtures/cases.json
"""
import itertools
import json
import sys
from datetime import date

# Each rule: (id, conditions, outcome, policy text). A condition value of None means "any".
# days is an upper bound (inclusive) or None for any.
RULES_V7 = [
    ("R-1", dict(damaged=True, sale=None, member=None, days=90), "refund", "Damaged on arrival: refund within 90 days"),
    ("R-2", dict(damaged=False, sale=True, member=None, days=30), "store_credit", "Sale items: store credit within 30 days"),
    ("R-3", dict(damaged=False, sale=False, member=True, days=45), "refund", "Members: refund within 45 days"),
    ("R-4", dict(damaged=False, sale=False, member=False, days=30), "refund", "Standard: refund within 30 days"),
    ("R-5", dict(damaged=None, sale=None, member=None, days=None), "refuse", "Outside every window"),
]
# v6: members had 30 days and sale items were refunded.
RULES_V6 = [
    ("R-1", dict(damaged=True, sale=None, member=None, days=90), "refund", "Damaged on arrival: refund within 90 days"),
    ("R-4", dict(damaged=False, sale=None, member=None, days=30), "refund", "Standard: refund within 30 days"),
    ("R-5", dict(damaged=None, sale=None, member=None, days=None), "refuse", "Outside every window"),
]
VERSIONS = [(date(2026, 1, 1), "v6", RULES_V6), (date(2026, 9, 1), "v7", RULES_V7)]
BOOLS = ("damaged", "sale", "member")


def matches(cond, facts):
    for k in BOOLS:
        if cond[k] is not None and cond[k] != facts[k]:
            return False
    return cond["days"] is None or facts["days"] <= cond["days"]


def table_for(delivered_on):
    chosen = None
    for start, name, rules in VERSIONS:
        if delivered_on >= start:
            chosen = (name, rules)
    return chosen


def evaluate(facts, delivered_on, hit_policy="FIRST"):
    chosen = table_for(delivered_on)
    if chosen is None:
        return {"outcome": "escalate", "reason": "no policy version for that date"}
    name, rules = chosen
    hits = [r for r in rules if matches(r[1], facts)]
    if not hits:
        return {"outcome": "escalate", "reason": "no rule matched", "version": name}
    if hit_policy == "UNIQUE" and len(hits) > 1:
        raise ValueError("UNIQUE table matched rules %s" % [h[0] for h in hits])
    rid, _, outcome, text = hits[0]
    return {"outcome": outcome, "rule": rid, "version": name, "policy_text": text}


def boundary_inputs(rules):
    """Every combination of boolean inputs and each day bound, the day after it and day 0."""
    days = sorted({0} | {r[1]["days"] for r in rules if r[1]["days"] is not None} | {r[1]["days"] + 1 for r in rules if r[1]["days"] is not None})
    for combo in itertools.product([True, False], repeat=3):
        for d in days:
            yield dict(zip(BOOLS, combo), days=d)


def check_table(rules):
    gaps, overlaps, wins = [], set(), {r[0]: 0 for r in rules}
    for facts in boundary_inputs(rules):
        hits = [r[0] for r in rules if matches(r[1], facts)]
        if not hits:
            gaps.append(facts)
            continue
        wins[hits[0]] += 1
        for a, b in itertools.combinations(hits, 2):
            overlaps.add((a, b))
    return {"gaps": gaps, "overlaps": sorted(overlaps), "unreachable": [r for r, n in wins.items() if n == 0]}


def diff_versions(old, new):
    changed = []
    for facts in boundary_inputs(old + new):
        a = next(r for r in old if matches(r[1], facts))
        b = next(r for r in new if matches(r[1], facts))
        if a[2] != b[2]:
            changed.append({"facts": facts, "old": a[2], "new": b[2], "new_rule": b[0]})
    return changed


def run(cases):
    out = {"cases": [], "check_v7": None, "check_v7_without_catch_all": None, "v6_to_v7_changes": None}
    for c in cases:
        r = evaluate(c["facts"], date.fromisoformat(c["delivered_on"]))
        out["cases"].append({"name": c["name"], **{k: r.get(k) for k in ("outcome", "rule", "version")}})
    chk = check_table(RULES_V7)
    out["check_v7"] = {"gaps": len(chk["gaps"]), "overlaps": [list(o) for o in chk["overlaps"]], "unreachable": chk["unreachable"]}
    chk2 = check_table(RULES_V7[:-1])
    out["check_v7_without_catch_all"] = {"gaps": len(chk2["gaps"]), "example_gap": chk2["gaps"][0] if chk2["gaps"] else None}
    out["v6_to_v7_changes"] = len(diff_versions(RULES_V6, RULES_V7))
    return out


if __name__ == "__main__":
    with open(sys.argv[1] if len(sys.argv) > 1 else "fixtures/cases.json", encoding="utf-8") as f:
        print(json.dumps(run(json.load(f)), indent=2))
