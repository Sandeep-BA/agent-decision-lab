"""Simulate the documented residency rules of SGLang 0.5.23 Paged Experts on synthetic MoE routing.

Author: Sandeep Belgavi. Original example for the aicassindra.com article "SGLang 0.5.23 Paged Experts: Serving
an MoE Model Larger Than GPU Memory". Written from the SGLang documentation and the behaviour of
paged_experts/residency.py (Apache-2.0): K slots per layer start holding experts 0..K-1; a step's distinct experts
are split into waves of at most K, resident experts first; each wave evicts the least recently used experts
outside it; every miss is one page-in. No SGLang code is copied, and no GPU or model is used.
Run: python paged.py fixtures/qwen3_30b_a3b_int4.json
"""
import json
import random
import sys
from collections import OrderedDict


class LRUSlots:
    def __init__(self, k):
        self.k = k
        self.resident = OrderedDict((e, e) for e in range(k))  # expert -> slot, least recently used first

    def place(self, wave):
        assert len(wave) <= self.k
        for e in wave:
            if e in self.resident:
                self.resident.move_to_end(e)
        loads = 0
        for e in wave:
            if e not in self.resident:
                _, slot = self.resident.popitem(last=False)  # never one of this wave: they are all at the tail
                self.resident[e] = slot
                loads += 1
        return loads

    def plan(self, distinct):
        hits = [e for e in distinct if e in self.resident]
        ordered = hits + [e for e in distinct if e not in self.resident]
        waves = [ordered[i:i + self.k] for i in range(0, len(ordered), self.k)] or [[]]
        return {"hits": len(hits), "loads": sum(self.place(w) for w in waves), "waves": len(waves)}


def router(n_experts, top_k, locality, skew, rng):
    weights = [1 / (r + 1) ** skew for r in range(n_experts)]
    order = list(range(n_experts))
    rng.shuffle(order)  # popular experts are not simply 0..K-1

    def route(prev):
        out = []
        for _ in range(top_k):
            pick = None
            if prev and rng.random() < locality:
                cands = [e for e in prev if e not in out]
                if cands:
                    pick = rng.choice(cands)
            while pick is None or pick in out:
                pick = order[rng.choices(range(n_experts), weights)[0]]
            out.append(pick)
        return out
    return route


def simulate(c, seed=7):
    if c["top_k"] > c["experts"] or not c["top_k"] <= c["resident"] <= c["experts"]:
        raise ValueError("need top_k <= K <= E")
    rng = random.Random(seed)
    route = router(c["experts"], c["top_k"], c["locality"], c["skew"], rng)
    slots = LRUSlots(c["resident"])
    prev, seen = [], set()
    for _ in range(c["prefill_tokens"]):
        prev = route(prev)
        seen.update(prev)
    pre = slots.plan(sorted(seen))
    last = [list(prev) for _ in range(c["batch"])]
    hits = distinct = loads = multi = 0
    for _ in range(c["decode_steps"]):
        step = set()
        for r in range(c["batch"]):
            last[r] = route(last[r])
            step.update(last[r])
        res = slots.plan(sorted(step))
        hits += res["hits"]; distinct += len(step); loads += res["loads"]; multi += res["waves"] > 1
    mb = lambda n: n * c["layers"] * c["expert_mb"]
    per_step_mb = mb(loads / c["decode_steps"])
    return {
        "decode_miss_rate_pct": round(100 * (1 - hits / distinct), 1),
        "paged_per_decode_step_mb": round(per_step_mb, 1),
        "transfer_ms_per_decode_step": round(per_step_mb / c["gbps"], 2),
        "prefill_paged_gb": round(mb(pre["loads"]) / 1000, 2),
        "prefill_waves": pre["waves"],
        "capture_limit_requests": c["resident"] // c["top_k"],
        "decode_captured": c["batch"] * c["top_k"] <= c["resident"],
        "decode_steps_with_several_waves": multi,
        "gpu_expert_gb": round(c["resident"] * c["layers"] * c["expert_mb"] / 1000, 2),
        "pinned_host_gb": round(c["experts"] * c["layers"] * c["expert_mb"] / 1000, 2),
    }


if __name__ == "__main__":
    with open(sys.argv[1] if len(sys.argv) > 1 else "fixtures/qwen3_30b_a3b_int4.json", encoding="utf-8") as f:
        cfg = json.load(f)
    print(json.dumps({name: simulate({**cfg["base"], **over}) for name, over in cfg["runs"].items()}, indent=2))
