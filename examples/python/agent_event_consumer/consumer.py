"""An agent decision step inside a partitioned event consumer.

Author: Sandeep Belgavi.

Companion to "Putting an Agent Step Inside an Existing Event Consumer" (aicassindra.com,
system design). The consumer keeps the guarantees of the deterministic handler it replaces:

- per-key order: never two events of one key in flight, never a later event before an earlier one;
- rate limits as backpressure: a 429 pauses only the affected partition until Retry-After;
- poison events are parked after N attempts, and later events of the same key are parked with them;
- offsets are committed only up to the first unfinished event of a partition;
- effects carry a key derived from (topic, partition, offset), so redelivery applies nothing twice.

Everything runs on a simulated clock with an in-memory log and a fake model. No model provider,
broker or network is used. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Event:
    topic: str
    partition: int
    offset: int
    key: str
    payload: dict


class RateLimited(Exception):
    def __init__(self, retry_after: float):
        super().__init__(f"429, retry after {retry_after}")
        self.retry_after = retry_after


class InvalidDecision(Exception):
    """The model answered, but the answer does not validate."""


@dataclass
class Outcome:
    kind: str  # applied | duplicate | held | parked | retry
    retry_after: float = 0.0

    @staticmethod
    def retry(after: float) -> "Outcome":
        return Outcome("retry", after)


Outcome.APPLIED = Outcome("applied")
Outcome.DUPLICATE = Outcome("duplicate")
Outcome.HELD = Outcome("held")
Outcome.PARKED = Outcome("parked")


class EffectStore:
    """The deterministic write path. apply_once is where a real system writes in one transaction
    with the effect key under a unique constraint."""

    def __init__(self):
        self.applied: dict[str, dict] = {}
        self.order: list[str] = []

    def contains(self, effect_id: str) -> bool:
        return effect_id in self.applied

    def apply_once(self, effect_id: str, decision: dict) -> bool:
        if effect_id in self.applied:
            return False
        self.applied[effect_id] = decision
        self.order.append(effect_id)
        return True


class FakeModel:
    """Allows `per_window` calls per `window` seconds; raises InvalidDecision for poison payloads."""

    def __init__(self, per_window: int, window: float = 10.0):
        self.per_window, self.window = per_window, window
        self.calls = defaultdict(int)
        self.total_calls = 0
        self.rejections = 0

    def decide(self, event: Event, now: float) -> dict:
        w = int(now // self.window)
        if self.calls[w] >= self.per_window:
            self.rejections += 1
            raise RateLimited((w + 1) * self.window - now)
        self.calls[w] += 1
        self.total_calls += 1
        if event.payload.get("poison"):
            raise InvalidDecision("decision does not match the schema: missing field action")
        return {"action": event.payload.get("expect", "refund"), "account": event.key}


class KeyedAgentConsumer:
    def __init__(self, model: FakeModel, effects: EffectStore, max_attempts: int = 3, retry_delay: float = 5.0):
        self.model, self.effects = model, effects
        self.max_attempts, self.retry_delay = max_attempts, retry_delay
        self.attempts: dict[str, int] = defaultdict(int)
        self.parked_keys: set[tuple[int, str]] = set()
        self.parking: list[tuple[Event, str]] = []
        self.now = 0.0

    def validate(self, decision: dict) -> dict:
        if decision.get("action") not in {"refund", "reject", "escalate"}:
            raise InvalidDecision(f"action {decision.get('action')!r} is not allowed")
        return decision

    def decide(self, event: Event) -> dict:
        return self.model.decide(event, self.now)

    def handle(self, event: Event) -> Outcome:
        effect_id = f"{event.topic}/{event.partition}/{event.offset}"
        if (event.partition, event.key) in self.parked_keys:
            self.parking.append((event, "earlier event of this key is parked"))
            return Outcome.HELD
        if self.effects.contains(effect_id):
            return Outcome.DUPLICATE
        try:
            decision = self.validate(self.decide(event))  # the only model call
        except RateLimited as limited:
            return Outcome.retry(limited.retry_after)  # the caller pauses the partition
        except InvalidDecision as bad:
            self.attempts[effect_id] += 1
            if self.attempts[effect_id] >= self.max_attempts:
                self.parked_keys.add((event.partition, event.key))
                self.parking.append((event, str(bad)))
                return Outcome.PARKED
            return Outcome.retry(self.retry_delay)
        self.effects.apply_once(effect_id, decision)
        return Outcome.APPLIED


@dataclass
class PartitionState:
    events: list[Event]
    committed: int = 0
    finished: set = field(default_factory=set)
    paused_until: float = 0.0
    position: int = 0


def run(log: dict[int, list[Event]], consumer: KeyedAgentConsumer, crash_at: float | None = None,
        commit_every: float | None = 5.0, tick: float = 1.0, horizon: float = 600.0) -> dict:
    """Drive the consumer over a simulated clock. Each tick, every unpaused partition offers its next
    unfinished event (strict per-partition order keeps the example short; the article discusses
    parallelism across keys). A 429 pauses only that partition until Retry-After.
    commit_every=None commits after every finished event; otherwise every `commit_every` seconds.
    A crash rewinds every partition to its committed offset, which redelivers finished events."""
    parts = {p: PartitionState(evs) for p, evs in log.items()}
    redelivered = 0
    pauses = 0
    crashed = False
    t = 0.0
    while t <= horizon:
        consumer.now = t
        if crash_at is not None and not crashed and t >= crash_at:
            crashed = True
            for st in parts.values():
                redelivered += sum(1 for o in st.finished if o >= st.committed)
                st.finished = {o for o in st.finished if o < st.committed}
                st.position = st.committed
        for p, st in parts.items():
            if st.position >= len(st.events) or t < st.paused_until:
                continue
            outcome = consumer.handle(st.events[st.position])
            if outcome.kind == "retry":
                st.paused_until = t + outcome.retry_after
                pauses += 1
                continue
            st.finished.add(st.position)
            st.position += 1
            if commit_every is None:
                st.committed = st.position
        if commit_every is not None and t % commit_every == 0:
            for st in parts.values():
                st.committed = st.position
        if all(st.position >= len(st.events) for st in parts.values()):
            for st in parts.values():
                st.committed = st.position
            break
        t += tick
    return {
        "finished_at": t,
        "effects_applied": len(consumer.effects.applied),
        "model_calls": consumer.model.total_calls,
        "rate_limited": consumer.model.rejections,
        "partition_pauses": pauses,
        "parked": [(e.partition, e.offset, e.key, why) for e, why in consumer.parking],
        "redelivered": redelivered,
        "effect_order": consumer.effects.order,
        "committed": {p: st.committed for p, st in parts.items()},
    }


def load_log(path: Path) -> dict[int, list[Event]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    log = {}
    for p, items in enumerate(data["partitions"]):
        log[p] = [Event(data["topic"], p, o, item["key"], item.get("payload", {})) for o, item in enumerate(items)]
    return log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the synthetic dispute stream through the consumer.")
    ap.add_argument("--fixture", default=str(HERE / "fixtures" / "disputes.json"))
    ap.add_argument("--per-window", type=int, default=6, help="model calls allowed per 10 s window")
    ap.add_argument("--crash-at", type=float, default=None)
    ap.add_argument("--commit", choices=["interval", "each"], default="interval")
    args = ap.parse_args(argv)
    consumer = KeyedAgentConsumer(FakeModel(args.per_window), EffectStore())
    result = run(load_log(Path(args.fixture)), consumer, crash_at=args.crash_at,
                 commit_every=5.0 if args.commit == "interval" else None)
    for k in ("finished_at", "effects_applied", "model_calls", "rate_limited", "partition_pauses", "redelivered", "committed"):
        print(f"{k}: {result[k]}")
    for item in result["parked"]:
        print("parked:", item)
    return 0


if __name__ == "__main__":
    sys.exit(main())
