"""Aggregate model-request attempt records into the four metrics the guide recommends.

Author: Sandeep Belgavi.
Usage: python metrics.py <requests.jsonl>
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def aggregate(records: list[dict]) -> dict:
    turns = {r["turn"] for r in records}
    per_model: dict[str, dict] = defaultdict(lambda: {"attempts": 0, "completed": 0, "failed": 0, "cancelled": 0,
                                                      "input_tokens": 0, "output_tokens": 0, "unknown_usage": 0,
                                                      "latency_sum": 0.0, "latency_n": 0})
    for r in records:
        m = per_model[r.get("model") or "unknown"]
        m["attempts"] += 1
        status = r.get("status")
        if status in ("completed", "failed", "cancelled"):
            m[status] += 1
        if r.get("input_tokens") is None and r.get("output_tokens") is None:
            m["unknown_usage"] += 1
        else:
            m["input_tokens"] += r.get("input_tokens") or 0
            m["output_tokens"] += r.get("output_tokens") or 0
        if r.get("latency_s") is not None:
            m["latency_sum"] += r["latency_s"]
            m["latency_n"] += 1
    return {
        "turns": len(turns),
        "attempts": len(records),
        "attempts_per_turn": (len(records) / len(turns)) if turns else 0.0,
        "models": dict(per_model),
    }


def render(summary: dict) -> str:
    lines = [f"turns={summary['turns']} attempts={summary['attempts']} attempts_per_turn={summary['attempts_per_turn']:.2f}"]
    for model, m in sorted(summary["models"].items()):
        line = (f"model={model} attempts={m['attempts']} completed={m['completed']} failed={m['failed']} "
                f"cancelled={m['cancelled']} input_tokens={m['input_tokens']} output_tokens={m['output_tokens']}")
        if m["unknown_usage"]:
            line += f" unknown_usage={m['unknown_usage']}"
        if m["latency_n"]:
            line += f" mean_latency_s={m['latency_sum'] / m['latency_n']:.3f}"
        lines.append(line)
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(render(aggregate(records)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
