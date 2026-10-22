"""Audit an agent loop's requests for prompt-cache prefix breaks, and estimate what they cost.

Author: Sandeep Belgavi. Companion to "Keeping the Prompt Cache Warm in Agent Loops" (aicassindra.com).

Two tools in one file:

* ``first_divergence(prev, cur)`` finds the first block at which two consecutive requests differ.
  Everything from that block onward cannot be read from a cache entry written by the previous request.
* ``simulate(requests)`` replays a sequence of requests against a simplified model of documented
  prefix-caching behaviour: entries are written only at breakpoints, a read looks back at most 20 blocks
  from each breakpoint for an entry that an earlier request wrote, entries expire after a TTL that each
  read refreshes, and prefixes below a minimum length are not cached. Cost multipliers default to
  1.25 for a 5-minute write and 0.1 for a read, relative to an uncached input token.

Blocks carry explicit token counts so no tokenizer is needed. The model is a teaching aid built from the
providers' documentation, not a reimplementation of any provider; check real usage fields
(``cache_creation_input_tokens``/``cache_read_input_tokens`` or ``cached_tokens``) in production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Block:
    label: str
    tokens: int
    content: str


@dataclass
class Request:
    at: float                       # seconds since the loop started
    blocks: list[Block]
    breakpoints: list[int] = field(default_factory=list)   # block indices that carry a cache marker


def prefix_hashes(blocks: list[Block]) -> list[str]:
    out, h = [], hashlib.sha256()
    for b in blocks:
        h.update(b.label.encode() + b"\0" + b.content.encode() + b"\0")
        out.append(h.copy().hexdigest())
    return out


def first_divergence(prev: list[Block], cur: list[Block]) -> int | None:
    """Index of the first differing block, or None when cur extends prev unchanged."""
    for i, (a, b) in enumerate(zip(prev, cur)):
        if a != b:
            return i
    return None if len(cur) >= len(prev) else len(cur)


def simulate(requests: list[Request], ttl: float = 300, min_tokens: int = 1024, lookback: int = 20,
             write_mult: float = 1.25, read_mult: float = 0.1) -> dict:
    cache: dict[str, float] = {}          # prefix hash -> expiry time
    rows, totals = [], dict(input=0, read=0, write=0, uncached=0)
    prev = None
    for n, req in enumerate(requests, 1):
        hashes = prefix_hashes(req.blocks)
        cum = [0]
        for b in req.blocks:
            cum.append(cum[-1] + b.tokens)
        for k in [k for k, exp in cache.items() if exp <= req.at]:
            del cache[k]
        hit = -1                                   # last block index covered by a cache read
        for bp in sorted(req.breakpoints, reverse=True):
            for i in range(bp, max(-1, bp - lookback), -1):
                if hashes[i] in cache:
                    hit = max(hit, i)
                    break
        if hit >= 0:
            cache[hashes[hit]] = req.at + ttl      # a read refreshes the entry
        read = cum[hit + 1]
        last_bp = max(req.breakpoints) if req.breakpoints else -1
        write = 0
        for bp in req.breakpoints:
            if bp > hit and cum[bp + 1] >= min_tokens:
                cache[hashes[bp]] = req.at + ttl
        if last_bp > hit and cum[last_bp + 1] >= min_tokens:
            write = cum[last_bp + 1] - read
        total = cum[-1]
        uncached = total - read - write
        div = None if prev is None else first_divergence(prev, req.blocks)
        rows.append(dict(request=n, at=req.at, input_tokens=total, read=read, write=write, uncached=uncached,
                         diverged_at=None if div is None else f"{div}:{req.blocks[div].label}" if div < len(req.blocks) else "truncated"))
        for k, v in (("input", total), ("read", read), ("write", write), ("uncached", uncached)):
            totals[k] += v
        prev = req.blocks
    cost = totals["read"] * read_mult + totals["write"] * write_mult + totals["uncached"]
    return dict(rows=rows, totals=totals,
                hit_rate_pct=round(100 * totals["read"] / totals["input"], 1),
                cost_vs_uncached_pct=round(100 * cost / totals["input"], 1))


# ---------------------------------------------------------------- synthetic agent loops
TOOLS = [Block("tool:" + name, 350, "schema-of-" + name) for name in ("search_orders", "get_order", "refund", "notify")]
SYSTEM = Block("system", 1800, "You are the refunds agent. Policy v14 ...")


def turn_blocks(turns: int) -> list[Block]:
    out = []
    for t in range(1, turns + 1):
        out += [Block(f"user{t}" if t == 1 else f"tool_result{t}", 400, f"payload-{t}"),
                Block(f"assistant{t}", 150, f"tool_call-{t}")]
    return out


def loop(variant: str, turns: int = 10, gap: float = 20.0) -> list[Request]:
    reqs = []
    for t in range(1, turns + 1):
        at = (t - 1) * gap
        tools = list(TOOLS)
        system = SYSTEM
        history = turn_blocks(t)[:-1]          # the request ends with the latest user/tool_result block
        if variant == "timestamp":
            system = Block("system", 1800, SYSTEM.content + f" Current time: {at:.0f}s")
        if variant == "tool_order" and t >= 5:
            tools = tools[1:] + tools[:1]      # e.g. tools built from an unordered set or a registry refresh
        if variant == "compaction" and t >= 6:
            history = [Block("summary", 600, "summary-of-turns-1-5")] + turn_blocks(t)[10:-1]
        if variant == "approval_pause" and t >= 6:
            at += 360                          # a six-minute wait for a human approval before turn 6
        blocks = tools + [system] + history
        static_end = len(tools)                # index of the system block: end of the static prefix
        reqs.append(Request(at, blocks, breakpoints=[static_end, len(blocks) - 1]))
    return reqs


VARIANTS = ("stable", "timestamp", "tool_order", "compaction", "approval_pause")


def main() -> None:
    ap = argparse.ArgumentParser(description="Prompt-cache prefix audit for synthetic agent loops.")
    ap.add_argument("--variant", choices=VARIANTS + ("all",), default="all")
    ap.add_argument("--ttl", type=float, default=300)
    ap.add_argument("--rows", action="store_true", help="print per-request rows")
    args = ap.parse_args()
    for v in (VARIANTS if args.variant == "all" else (args.variant,)):
        r = simulate(loop(v), ttl=args.ttl)
        line = dict(variant=v, hit_rate_pct=r["hit_rate_pct"], cost_vs_uncached_pct=r["cost_vs_uncached_pct"], **r["totals"])
        print(json.dumps(line))
        if args.rows:
            for row in r["rows"]:
                print("   ", json.dumps(row))


if __name__ == "__main__":
    main()
