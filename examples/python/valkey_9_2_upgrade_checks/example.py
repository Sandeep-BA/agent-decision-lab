"""Two Valkey 9.2 behaviour changes as checkable models. Author: Sandeep Belgavi.

1. Score bounds (valkey-io/valkey PR 4054): before 9.2 a bare "(" parsed as "(0" and an
   empty string as 0 for ZRANGEBYSCORE, ZREVRANGEBYSCORE, ZCOUNT and ZRANGESTORE; 9.2
   returns "min or max is not a float". `parse_bound` models both versions.
2. Save points (PR 3118): 9.2 increments the dirty counter when active expiry deletes keys
   or hash fields on the primary, so `save <seconds> <changes>` rules can fire on expiry
   alone. `first_save` computes when a rule set would fire for a synthetic workload.
These are models of the merged changes, not runs against Valkey binaries.
"""
import json
import math


def parse_bound(text, version="9.2"):
    """Return (value, exclusive) or raise ValueError like the server's 'not a float' error."""
    exclusive = text.startswith("(")
    body = text[1:] if exclusive else text
    if body == "":
        if version == "9.2":
            raise ValueError("min or max is not a float")
        return 0.0, exclusive  # pre-9.2: zero-length number parsed as 0
    if body in ("+inf", "inf"):
        return math.inf, exclusive
    if body == "-inf":
        return -math.inf, exclusive
    try:
        return float(body), exclusive
    except ValueError:
        raise ValueError("min or max is not a float") from None


def zcount(scores, lo, hi, version="9.2"):
    (a, ax), (b, bx) = parse_bound(lo, version), parse_bound(hi, version)
    return sum(1 for s in scores if (s > a if ax else s >= a) and (s < b if bx else s <= b))


def audit_bounds(bounds):
    """Bounds a client sends that change meaning on upgrade (accepted before, rejected now)."""
    changed = []
    for b in bounds:
        try:
            parse_bound(b, "9.2")
        except ValueError:
            try:
                old = parse_bound(b, "9.0")
                changed.append({"bound": b, "before_9_2": old, "from_9_2": "error: min or max is not a float"})
            except ValueError:
                pass
    return changed


def first_save(rules, writes_per_s, expiries_per_s, horizon_s=7200, count_expiry=True):
    """rules: [(seconds, changes)]. Returns the first second at which any rule is satisfied
    after the last save at t=0, or None. Dirty grows by writes (+ expiries when counted)."""
    rate = writes_per_s + (expiries_per_s if count_expiry else 0)
    best = None
    for seconds, changes in rules:
        if rate == 0:
            continue
        t = max(seconds, math.ceil(changes / rate))
        if t <= horizon_s and (best is None or t < best):
            best = t
    return best


def demo():
    rules = [(3600, 1), (300, 100), (60, 10000)]  # a common save line, synthetic workload below
    return {
        "zcount_bare_paren": {"9.0": zcount([0, 0.5, 1, 2], "(", "+inf", "9.0"),
                              "9.2": "error: min or max is not a float"},
        "audit": audit_bounds(["(", "", "(5", "-inf", "(abc", "+inf"]),
        "first_save_s_read_only_cache_50_expiries_per_s": {
            "before_9_2_primary": first_save(rules, 0.0, 50, count_expiry=False),
            "from_9_2_primary": first_save(rules, 0.0, 50, count_expiry=True),
        },
    }


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
