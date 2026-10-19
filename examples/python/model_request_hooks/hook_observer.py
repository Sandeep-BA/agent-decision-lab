"""Observation-only hook handler for PreModelRequest and PostModelRequest events.

Author: Sandeep Belgavi. Reads one JSON event on stdin, writes one JSON Lines record per
completed attempt, and prints nothing on stdout: an observer must never look like a control
directive. Diagnostics go to stderr.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def state_dir() -> Path:
    return Path(os.environ.get("HOOK_STATE_DIR", Path.home() / ".cache" / "model-request-hook"))


def handle(event: dict, now: float | None = None, directory: Path | None = None) -> dict | None:
    """Process one event. Returns the record written for a post event, None for a pre event."""
    now = time.time() if now is None else now
    directory = directory or state_dir()
    directory.mkdir(parents=True, exist_ok=True)
    name = event["hook_event_name"]
    turn = event["turn_id"]
    marker = directory / f"{turn}.start"
    if name == "PreModelRequest":
        marker.write_text(repr(now), encoding="utf-8")
        return None
    if name != "PostModelRequest":
        return None
    started = float(marker.read_text(encoding="utf-8")) if marker.exists() else None
    usage = event.get("token_usage")
    record = {
        "turn": turn,
        "session": event.get("session_id"),
        "model": event.get("model"),
        "agent_type": event.get("agent_type") or "root",
        "status": event.get("status"),
        "error": event.get("error"),
        "latency_s": None if started is None else round(now - started, 3),
        # null usage means unknown, never zero: a cancelled attempt may have consumed tokens
        "input_tokens": usage.get("input_tokens") if isinstance(usage, dict) else None,
        "output_tokens": usage.get("output_tokens") if isinstance(usage, dict) else None,
    }
    with open(directory / "requests.jsonl", "a", encoding="utf-8") as out:
        out.write(json.dumps(record) + "\n")
    if marker.exists():
        marker.unlink()
    return record


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"model-request-hook: invalid JSON on stdin: {exc}", file=sys.stderr)
        return 1
    record = handle(event)
    if record is not None:
        print(json.dumps(record), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
