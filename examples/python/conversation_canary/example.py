"""Canary a prompt or model change per conversation, not per request. Author: Sandeep Belgavi.

Assignment uses a 32-bit FNV-1a hash of "<salt>:<conversation_id>" mapped to a bucket in
0..9999. A conversation is in treatment when bucket < ramp_basis_points. Raising the ramp
only moves conversations from control to treatment; lowering it (a rollback) only moves them
back. Even so, recomputing on every turn moves a conversation that is open while the ramp
changes, so the variant is also pinned when the conversation starts. Three policies are
compared: per-request random, hash recomputed each turn, and hash pinned at the first turn.
Synthetic ids, no model calls.
"""
import json
import random

BUCKETS = 10_000


def fnv1a32(text):
    h = 0x811C9DC5
    for byte in text.encode("utf-8"):
        h ^= byte
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def bucket(conversation_id, salt):
    return fnv1a32(f"{salt}:{conversation_id}") % BUCKETS


def assign(conversation_id, salt, ramp_bp):
    if not 0 <= ramp_bp <= BUCKETS:
        raise ValueError("ramp_bp must be within 0..10000")
    return "treatment" if bucket(conversation_id, salt) < ramp_bp else "control"


def simulate(policy="pinned", conversations=400, turns=6, schedule=(500, 2000, 5000),
             salt="prompt-v7", seed=11, salt_change_at=None):
    """Every conversation has `turns` turns; the ramp steps through `schedule` evenly over
    those turns. policy: "request" (random per request), "hash" (recomputed per turn) or
    "pinned" (hash at the first turn, stored, reused). Returns switching counts."""
    if policy not in {"request", "hash", "pinned"}:
        raise ValueError("unknown policy")
    rng = random.Random(seed)
    ids = [f"CASE-{4000 + i}" for i in range(conversations)]
    seen = {cid: [] for cid in ids}
    pinned = {}
    for t in range(turns):
        ramp = schedule[min(len(schedule) - 1, t * len(schedule) // turns)]
        current_salt = salt if salt_change_at is None or t < salt_change_at else salt + "-b"
        for cid in ids:
            if policy == "request":
                variant = "treatment" if rng.random() * BUCKETS < ramp else "control"
            elif policy == "hash":
                variant = assign(cid, current_salt, ramp)
            else:
                variant = pinned.setdefault(cid, assign(cid, current_salt, ramp))
            seen[cid].append(variant)
    mixed = [cid for cid, v in seen.items() if len(set(v)) > 1]
    backwards = [cid for cid, v in seen.items()
                 if any(a == "treatment" and b == "control" for a, b in zip(v, v[1:]))]
    return {"policy": policy, "conversations": conversations, "turns": turns,
            "mixed_conversations": len(mixed), "treatment_to_control_switches": len(backwards),
            "treatment_at_first_turn": sum(1 for v in seen.values() if v[0] == "treatment"),
            "treatment_at_last_turn": sum(1 for v in seen.values() if v[-1] == "treatment")}


def new_conversation_share(ramp_bp, salt="prompt-v7", n=10_000):
    """Share of fresh conversation ids assigned to treatment at a fixed ramp."""
    return sum(assign(f"NEW-{i}", salt, ramp_bp) == "treatment" for i in range(n)) / n


def demo():
    return {
        "per_request_random": simulate("request"),
        "hash_recomputed_each_turn": simulate("hash"),
        "hash_pinned_at_first_turn": simulate("pinned"),
        "hash_recomputed_with_salt_change": simulate("hash", schedule=(2000,), salt_change_at=3),
        "new_conversation_share_at_2000bp": new_conversation_share(2000),
        "example_assignments": {cid: [assign(cid, "prompt-v7", r) for r in (500, 2000, 5000)]
                                for cid in ("CASE-4001", "CASE-4002", "CASE-4003")},
    }


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
