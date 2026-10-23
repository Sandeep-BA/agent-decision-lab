"""A level-triggered reconciler driven by an agent-written desired state.

Author: Sandeep Belgavi.

The agent emits a desired state (a set of grants with an expiry). This module is the deterministic
reconciler: it reads the current state, computes the difference, and applies only the changes that
close the gap. It is idempotent and restartable, so a crash mid-pass is recovered by the next pass.

Standard library only. No network, no API, no credentials. Everything here is synthetic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


@dataclass
class Store:
    """A synthetic current-state store. Applies are keyed, so repeats are safe when idempotent=True."""

    idempotent: bool = True
    grants: dict[str, int] = field(default_factory=dict)   # key -> times applied

    def current(self) -> set[str]:
        return {k for k, n in self.grants.items() if n > 0}

    def add(self, key: str) -> None:
        if self.idempotent:
            self.grants[key] = 1
        else:
            self.grants[key] = self.grants.get(key, 0) + 1

    def remove(self, key: str) -> None:
        self.grants[key] = 0

    def duplicate_count(self) -> int:
        return sum(max(0, n - 1) for n in self.grants.values())


@dataclass
class ReconcileResult:
    changes: int
    passes: int
    gap: int
    duplicate_applies: int
    converged: bool


def active_set(desired: dict, now: datetime) -> set[str]:
    """The grants that should exist right now: empty once the desired state has expired."""
    if now >= _iso(desired["expires_at"]):
        return set()
    return {f"{g['project']}:{g['role']}" for g in desired["grants"]}


def reconcile_once(desired, store, now, *, read_current=None, crash_after=None):
    """One level-triggered pass. Returns the number of changes applied.

    read_current lets a caller inject a stale (lagging) view; defaults to the real current state.
    crash_after stops the pass after N applied changes to simulate a crash mid-pass.
    """
    active = active_set(desired, now)
    observed = store.current() if read_current is None else read_current
    adds = sorted(active - observed)
    removes = sorted(observed - active)
    applied = 0
    for key in adds:
        if crash_after is not None and applied >= crash_after:
            return applied
        store.add(key)
        applied += 1
    for key in removes:
        if crash_after is not None and applied >= crash_after:
            return applied
        store.remove(key)
        applied += 1
    return applied


def reconcile(desired, store, now, *, passes=2, crash_after=None, stale=False) -> ReconcileResult:
    """Run the loop for `passes` passes. A crash is applied on pass 1 only.

    When stale=True the reconciler reads a view that lags one pass behind its own writes, which is
    harmless when applies are idempotent and causes duplicate applies when they are not.
    """
    total = 0
    observed_prev: set[str] = set()
    for p in range(1, passes + 1):
        read_current = observed_prev if (stale and p > 1) else None
        ca = crash_after if p == 1 else None
        observed_now = store.current() if read_current is None else read_current
        total += reconcile_once(desired, store, now, read_current=read_current, crash_after=ca)
        observed_prev = observed_now
    active = active_set(desired, now)
    cur = store.current()
    gap = len(active - cur) + len(cur - active)
    dups = store.duplicate_count()
    return ReconcileResult(changes=total, passes=passes, gap=gap,
                           duplicate_applies=dups, converged=(gap == 0 and dups == 0))


def demo():
    desired = {
        "principal": "contractor:erika",
        "grants": [{"project": "atlas", "role": "reader"},
                   {"project": "orion", "role": "reader"},
                   {"project": "vega", "role": "reader"}],
        "expires_at": "2026-10-30T00:00:00Z",
    }
    now = datetime(2026, 10, 23, tzinfo=timezone.utc)
    store = Store()
    store.add("legacy1:reader")                       # external drift
    res = reconcile(desired, store, now, passes=2, crash_after=1)
    print("default:", res)
    return res


if __name__ == "__main__":
    demo()
