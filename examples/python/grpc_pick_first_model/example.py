"""Author: Sandeep Belgavi. Model of the first connection pass of gRPC Java's pick_first policy (v1.86.0).

Read from the v1.86.0 sources of PickFirstLoadBalancerProvider and PickFirstLeafLoadBalancer:
  - GRPC_EXPERIMENTAL_ENABLE_NEW_PICK_FIRST now defaults to true, so the leaf balancer is used.
  - The leaf balancer removes duplicate addresses and creates one subchannel per address.
  - Happy Eyeballs is used only when GRPC_PF_USE_HAPPY_EYEBALLS is true (default false). Then the
    flattened list is interleaved by address family, starting with the family of the first address,
    and a new attempt starts every CONNECTION_DELAY_INTERVAL_MS = 250 ms while earlier ones continue.
  - Without Happy Eyeballs, addresses are tried one at a time in list order.
  - When every address has failed once, the balancer reports TRANSIENT_FAILURE and asks the name
    resolver to refresh.
This is a timeline model for teaching, not gRPC: no sockets, backoff or real resolver are involved.
"""
import json

DELAY_MS = 250


def dedup(addresses):
    seen, out = set(), []
    for a in addresses:
        if a["addr"] not in seen:
            seen.add(a["addr"])
            out.append(a)
    return out


def interleave(addresses):
    if not addresses:
        return []
    first = addresses[0]["family"]
    a = [x for x in addresses if x["family"] == first]
    b = [x for x in addresses if x["family"] != first]
    out = []
    for i in range(max(len(a), len(b))):
        if i < len(a):
            out.append(a[i])
        if i < len(b):
            out.append(b[i])
    return out


def first_pass(addresses, happy_eyeballs: bool, connect_timeout_ms: int):
    """Return the time to READY (or failure), the chosen address and a trace of decisions."""
    trace, order = [], dedup(addresses)
    if len(order) < len(addresses):
        trace.append(f"0 ms: removed {len(addresses) - len(order)} duplicate address(es)")
    if happy_eyeballs:
        order = interleave(order)
    trace.append("0 ms: attempt order " + ", ".join(a["addr"] for a in order))

    def finish(a, start):
        dur = a["ms"] if a["outcome"] in ("ok", "refused") else connect_timeout_ms
        return start + dur, a["outcome"] == "ok"

    attempts = []
    if not happy_eyeballs:
        t = 0
        for a in order:
            end, ok = finish(a, t)
            attempts.append((a, t, end, ok))
            trace.append(f"{t} ms: connect {a['addr']} -> " + ("READY" if ok else ("refused" if a["outcome"] == "refused" else "timed out")) + f" at {end} ms")
            if ok:
                return {"ready_ms": end, "address": a["addr"], "attempts_started": len(attempts), "max_parallel": 1,
                        "state": "READY", "reresolution_requests": 0, "trace": trace}
            t = end
        trace.append(f"{t} ms: every address failed once -> TRANSIENT_FAILURE, refresh name resolution")
        return {"ready_ms": None, "failed_ms": t, "address": None, "attempts_started": len(attempts), "max_parallel": 1,
                "state": "TRANSIENT_FAILURE", "reresolution_requests": 1, "trace": trace}

    # Happy Eyeballs: start i-th attempt at the earlier of i*250 ms (timer) or when every earlier
    # attempt has failed (failure moves to the next address immediately).
    starts, ends, results = [], [], []
    next_start = 0
    for i, a in enumerate(order):
        if i > 0:
            timer = starts[-1] + DELAY_MS
            all_failed_by = max(ends) if all(not r for r in results) else float("inf")
            prev_failed_at = ends[-1] if not results[-1] else float("inf")
            next_start = min(timer, prev_failed_at) if prev_failed_at < float("inf") else timer
            ready_so_far = [e for e, r in zip(ends, results) if r]
            if ready_so_far and min(ready_so_far) <= next_start:
                break
        end, ok = finish(a, next_start)
        starts.append(next_start); ends.append(end); results.append(ok)
        why = "first address" if i == 0 else ("previous attempt failed" if next_start < starts[-2] + DELAY_MS else "250 ms timer fired")
        trace.append(f"{next_start} ms: start {a['addr']} ({why}) -> " + ("READY" if ok else "fails") + f" at {end} ms")
    ready = [(e, i) for i, (e, r) in enumerate(zip(ends, results)) if r]
    if ready:
        t, i = min(ready)
        inflight = sum(1 for s, e in zip(starts, ends) if s <= t < e or (s <= t and e == t))
        trace.append(f"{t} ms: {order[i]['addr']} READY first; cancel timer, shut down {len(starts) - 1} other subchannel(s)")
        par = max(sum(1 for s2, e2 in zip(starts, ends) if s2 <= s < e2) for s in starts)
        return {"ready_ms": t, "address": order[i]["addr"], "attempts_started": len(starts), "max_parallel": par,
                "state": "READY", "reresolution_requests": 0, "trace": trace}
    t = max(ends)
    trace.append(f"{t} ms: every address failed once -> TRANSIENT_FAILURE, refresh name resolution")
    par = max(sum(1 for s2, e2 in zip(starts, ends) if s2 <= s < e2) for s in starts)
    return {"ready_ms": None, "failed_ms": t, "address": None, "attempts_started": len(starts), "max_parallel": par,
            "state": "TRANSIENT_FAILURE", "reresolution_requests": 1, "trace": trace}


SCENARIOS = {
    "ipv6 blackholed": [
        {"addr": "[2001:db8::10]:443", "family": "v6", "outcome": "timeout", "ms": 0},
        {"addr": "[2001:db8::11]:443", "family": "v6", "outcome": "timeout", "ms": 0},
        {"addr": "192.0.2.10:443", "family": "v4", "outcome": "ok", "ms": 30},
        {"addr": "192.0.2.11:443", "family": "v4", "outcome": "ok", "ms": 35},
    ],
    "first address refused, duplicates": [
        {"addr": "192.0.2.20:443", "family": "v4", "outcome": "refused", "ms": 2},
        {"addr": "192.0.2.20:443", "family": "v4", "outcome": "refused", "ms": 2},
        {"addr": "192.0.2.21:443", "family": "v4", "outcome": "ok", "ms": 40},
    ],
    "all down": [
        {"addr": "192.0.2.30:443", "family": "v4", "outcome": "refused", "ms": 3},
        {"addr": "[2001:db8::30]:443", "family": "v6", "outcome": "timeout", "ms": 0},
    ],
}


def main(connect_timeout_ms: int = 20_000):
    out = {}
    for name, addrs in SCENARIOS.items():
        out[name] = {"serial (1.86 default)": first_pass(addrs, False, connect_timeout_ms),
                     "happy eyeballs (GRPC_PF_USE_HAPPY_EYEBALLS=true)": first_pass(addrs, True, connect_timeout_ms)}
    print(json.dumps({k: {p: {x: y for x, y in r.items() if x != "trace"} for p, r in v.items()} for k, v in out.items()}, indent=2))
    return out


if __name__ == "__main__":
    main()
