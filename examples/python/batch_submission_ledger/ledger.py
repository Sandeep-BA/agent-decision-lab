"""A submission ledger for provider batch APIs: chunk, submit, reconcile by custom_id, resubmit.

Author: Sandeep Belgavi.

Companion to "Moving Deferrable Agent Work to Provider Batch APIs" (aicassindra.com, llm).
The ledger owns the truth about every work item. Providers are simulated with the documented
behaviour that differs between them when a batch does not finish in its window:

- "openai":    the batch expires; finished requests are in the output file, unfinished ones are
               listed in the error file with code batch_expired.
- "anthropic": each request ends as succeeded, errored, canceled or expired.
- "gemini":    a job pending or running for more than 48 hours expires with no results at all.

Results arrive in arbitrary order and are matched by custom_id only. Standard library only; no
provider is called and nothing here is a statement about real provider latency or pricing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
CUSTOM_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")  # the strictest documented format (Anthropic)
RETRYABLE = {"expired", "server_error", "canceled"}


@dataclass
class Item:
    item_id: str
    prompt: str
    state: str = "pending"  # pending | submitted | done | review
    batch_id: str | None = None
    attempts: int = 0
    last_error: str = ""
    result: str | None = None

    @property
    def custom_id(self) -> str:
        cid = f"{self.item_id}-a{self.attempts}"
        assert CUSTOM_ID.match(cid), cid
        return cid


@dataclass
class Ledger:
    items: dict[str, Item] = field(default_factory=dict)
    batches: dict[str, list[str]] = field(default_factory=dict)
    applied: dict[str, str] = field(default_factory=dict)  # downstream store, keyed by item_id

    def add(self, item_id: str, prompt: str) -> None:
        if item_id not in self.items:  # adding twice is a no-op
            self.items[item_id] = Item(item_id, prompt)

    def plan(self, max_requests: int, max_bytes: int, max_attempts: int = 3) -> list[list[Item]]:
        """Chunk eligible items into batches under both limits."""
        eligible = [i for i in self.items.values() if i.state == "pending" and i.attempts < max_attempts]
        batches, current, size = [], [], 0
        for item in eligible:
            line = len(json.dumps({"custom_id": item.custom_id, "body": item.prompt}).encode()) + 1
            if current and (len(current) >= max_requests or size + line > max_bytes):
                batches.append(current)
                current, size = [], 0
            current.append(item)
            size += line
        if current:
            batches.append(current)
        return batches

    def submit(self, provider: "FakeProvider", batch: list[Item]) -> str:
        for item in batch:
            item.attempts += 1  # the custom_id carries the attempt, so a resubmission never collides
        batch_id = provider.create([(i.custom_id, i.prompt) for i in batch])
        for item in batch:
            item.state, item.batch_id = "submitted", batch_id
        self.batches[batch_id] = [i.item_id for i in batch]
        return batch_id

    def reconcile(self, batch_id: str, results: list[dict], max_attempts: int = 3) -> dict:
        """Apply one batch's results. Matching is by custom_id; anything not reported goes back to
        pending (or review after max_attempts). Re-running with the same results changes nothing."""
        expected = {self.items[i].custom_id: self.items[i] for i in self.batches[batch_id]
                    if self.items[i].batch_id == batch_id and self.items[i].state == "submitted"}
        counts = {"succeeded": 0, "retry": 0, "review": 0, "unknown": 0, "already_applied": 0}
        reported = set()
        for r in results:
            item = expected.get(r["custom_id"])
            if item is None:
                counts["unknown"] += 1
                continue
            reported.add(r["custom_id"])
            if r["type"] == "succeeded":
                if item.item_id in self.applied:
                    counts["already_applied"] += 1
                else:
                    self.applied[item.item_id] = r["text"]
                item.state, item.result = "done", r["text"]
                counts["succeeded"] += 1
            else:
                self._fail(item, r["type"], max_attempts, counts)
        for cid, item in expected.items():
            if cid not in reported:
                self._fail(item, "missing from results", max_attempts, counts)
        return counts

    @staticmethod
    def _fail(item: Item, why: str, max_attempts: int, counts: dict) -> None:
        item.last_error = why
        retryable = why in RETRYABLE or why == "missing from results"
        if retryable and item.attempts < max_attempts:
            item.state = "pending"
            counts["retry"] += 1
        else:
            item.state = "review"
            counts["review"] += 1

    def summary(self) -> dict:
        out = {}
        for item in self.items.values():
            out[item.state] = out.get(item.state, 0) + 1
        return dict(sorted(out.items()))


class FakeProvider:
    """Simulates one provider's end-of-window behaviour. `finish` is the share of requests that
    complete before the window closes; `invalid` marks prompts that always error."""

    def __init__(self, kind: str, finish: float, seed: int = 7):
        assert kind in {"openai", "anthropic", "gemini"}
        self.kind, self.finish, self.rng = kind, finish, random.Random(seed)
        self.jobs: dict[str, list[tuple[str, str]]] = {}

    def create(self, requests: list[tuple[str, str]]) -> str:
        batch_id = "batch_" + hashlib.sha256(json.dumps(requests).encode()).hexdigest()[:10]
        self.jobs[batch_id] = requests
        return batch_id

    def results(self, batch_id: str) -> list[dict]:
        requests = self.jobs[batch_id]
        done = int(len(requests) * self.finish)
        self.finish = 1.0  # only the first batch runs into the end of its window
        if self.kind == "gemini" and done < len(requests):
            return []  # the whole job expired: no results to retrieve
        out = []
        for n, (cid, prompt) in enumerate(requests):
            if "INVALID" in prompt:
                out.append({"custom_id": cid, "type": "invalid_request"})
            elif n < done:
                out.append({"custom_id": cid, "type": "succeeded", "text": f"summary of {prompt[:24]}"})
            else:  # openai: error file with code batch_expired; anthropic: result type expired
                out.append({"custom_id": cid, "type": "expired"})
        self.rng.shuffle(out)  # documented: output order may not match input order
        return out


def run(kind: str, n_items: int = 12, finish: float = 0.5, max_requests: int = 5, max_bytes: int = 10_000) -> dict:
    ledger = Ledger()
    for k in range(n_items):
        ledger.add(f"ticket-{k:03d}", f"Summarise ticket {k:03d}" + (" INVALID" if k == 7 else ""))
    provider = FakeProvider(kind, finish)
    rounds = []
    for _round in range(4):
        batches = ledger.plan(max_requests, max_bytes)
        if not batches:
            break
        for batch in batches:
            batch_id = ledger.submit(provider, batch)
            rounds.append(ledger.reconcile(batch_id, provider.results(batch_id)))
    return {"provider": kind, "rounds": rounds, "summary": ledger.summary(), "applied": len(ledger.applied),
            "attempts": sum(i.attempts for i in ledger.items.values())}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Simulate submitting and reconciling deferred work.")
    ap.add_argument("--provider", choices=["openai", "anthropic", "gemini"], default="openai")
    ap.add_argument("--finish", type=float, default=0.5, help="share of each first batch done before the window closes")
    args = ap.parse_args(argv)
    result = run(args.provider, finish=args.finish)
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
