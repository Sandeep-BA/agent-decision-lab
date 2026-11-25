"""A model of the documented Kubernetes topology spread filter. Author: Sandeep Belgavi.

Rule modelled (DoNotSchedule): a domain d is feasible for an incoming matching pod when
    count[d] + 1 - global_min <= max_skew
where global_min is the minimum matching-pod count over eligible domains, or 0 when the
number of eligible domains is less than min_domains. Eligible domains are zones that still
have nodes; a zone whose nodes are all tainted (for example NotReady after an outage) and
not tolerated still counts as eligible under nodeTaintsPolicy Ignore (the documented
default when the field is null) and is excluded under Honor. ScheduleAnyway never filters;
it prefers the domain with the lowest resulting skew. Capacity (free pod slots per zone) is
a separate filter. This is a teaching model of the rules in the Kubernetes documentation,
not the scheduler's code; it ignores node-level placement, affinity, nodeAffinityPolicy,
per-pod tolerations, terminating-pod accounting and scoring weights.
"""
import json


def place(replicas, zones, max_skew=1, when="DoNotSchedule", min_domains=1, existing=None,
          tainted=(), taints_policy="Ignore"):
    """zones: {name: free_slots or None if the zone has no nodes}; tainted: zones whose nodes
    are all tainted and not tolerated (no usable capacity). Returns the placement trace.
    Assumes pods from a failed zone are no longer counted."""
    if max_skew < 1 or min_domains < 1:
        raise ValueError("max_skew and min_domains must be >= 1")
    if when not in {"DoNotSchedule", "ScheduleAnyway"}:
        raise ValueError("unknown whenUnsatisfiable")
    if taints_policy not in {"Ignore", "Honor"}:
        raise ValueError("unknown nodeTaintsPolicy")
    eligible = [z for z, free in zones.items() if free is not None
                and not (z in tainted and taints_policy == "Honor")]
    count = {z: (existing or {}).get(z, 0) for z in eligible}
    free = {z: (0 if z in tainted else zones[z]) for z in eligible}
    trace, pending = [], 0
    for n in range(replicas):
        global_min = 0 if len(eligible) < min_domains else min(count.values(), default=0)
        options = []
        for z in sorted(eligible):
            skew = count[z] + 1 - global_min
            fits = free[z] > 0
            ok = fits and (when == "ScheduleAnyway" or skew <= max_skew)
            options.append({"zone": z, "skew_if_placed": skew, "has_capacity": fits, "feasible": ok})
        feasible = [o for o in options if o["feasible"]]
        if not feasible:
            pending += 1
            trace.append({"pod": n + 1, "global_min": global_min, "placed": None, "options": options})
            continue
        best = min(feasible, key=lambda o: (o["skew_if_placed"], o["zone"]))
        count[best["zone"]] += 1
        free[best["zone"]] -= 1
        trace.append({"pod": n + 1, "global_min": global_min, "placed": best["zone"], "options": options})
    return {"counts": count, "pending": pending, "trace": trace}


def demo():
    healthy = place(6, {"zone-a": 4, "zone-b": 4, "zone-c": 4})
    # zone-c lost: its two pods are recreated; zone-a and zone-b already hold two each.
    lost = place(2, {"zone-a": 4, "zone-b": 4, "zone-c": None}, existing={"zone-a": 2, "zone-b": 2})
    lost_min3 = place(2, {"zone-a": 4, "zone-b": 4, "zone-c": None}, min_domains=3,
                      existing={"zone-a": 2, "zone-b": 2})
    tight = place(2, {"zone-a": 2, "zone-b": 0, "zone-c": None}, existing={"zone-a": 2, "zone-b": 2})
    tight_anyway = place(2, {"zone-a": 2, "zone-b": 0, "zone-c": None}, when="ScheduleAnyway",
                         existing={"zone-a": 2, "zone-b": 2})
    zone_c_tainted_ignore = place(2, {"zone-a": 4, "zone-b": 4, "zone-c": 4}, tainted={"zone-c"},
                                  existing={"zone-a": 2, "zone-b": 2})
    zone_c_tainted_honor = place(2, {"zone-a": 4, "zone-b": 4, "zone-c": 4}, tainted={"zone-c"},
                                 taints_policy="Honor", existing={"zone-a": 2, "zone-b": 2})
    return {name: {"counts": r["counts"], "pending": r["pending"]} for name, r in
            [("healthy_3_zones", healthy), ("zone_c_lost", lost), ("zone_c_lost_min_domains_3", lost_min3),
             ("zone_c_lost_b_full_DoNotSchedule", tight), ("zone_c_lost_b_full_ScheduleAnyway", tight_anyway),
             ("zone_c_nodes_tainted_policy_Ignore", zone_c_tainted_ignore),
             ("zone_c_nodes_tainted_policy_Honor", zone_c_tainted_honor)]}


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
