"""A change budget for agent writes: a deterministic cap on committed change per window.

Author: Sandeep Belgavi.

Per-call authorization answers whether one change is allowed. A change budget bounds the aggregate:
it counts every committed change by blast radius and halts the agent when the cap is reached,
regardless of whether each change was individually allowed.

Standard library only. No network, no model, no credentials. The agent here is a synthetic stub.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChangeBudget:
    """Deterministic cap on committed change within a window, measured by blast radius."""

    limits: dict[str, int]
    approve_fraction: float = 0.8
    spent: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self.spent = {k: 0 for k in self.limits}

    def check(self, cost: dict[str, int]) -> str:
        """Called before a write commits. Returns 'allow', 'approve' or 'halt'."""
        projected = {k: self.spent[k] + cost.get(k, 0) for k in self.limits}
        if any(projected[k] > self.limits[k] for k in self.limits):
            return "halt"
        if any(projected[k] > self.approve_fraction * self.limits[k] for k in self.limits):
            return "approve"
        return "allow"

    def commit(self, cost: dict[str, int]) -> None:
        for k in self.limits:
            self.spent[k] += cost.get(k, 0)


@dataclass
class RunResult:
    committed: int
    halted: bool
    approvals: int
    spent: dict[str, int]


def run_agent(budget: ChangeBudget, changes, *, auto_approve=False) -> RunResult:
    """Drive a sequence of (name, cost) changes through the budget.

    Each change is assumed individually authorized; the budget is the only thing that can stop it.
    An 'approve' routes to a human: with auto_approve the run continues, otherwise it stops there.
    """
    committed = 0
    approvals = 0
    for _name, cost in changes:
        decision = budget.check(cost)
        if decision == "halt":
            return RunResult(committed, True, approvals, dict(budget.spent))
        if decision == "approve":
            approvals += 1
            if not auto_approve:
                return RunResult(committed, False, approvals, dict(budget.spent))
        budget.commit(cost)
        committed += 1
    return RunResult(committed, False, approvals, dict(budget.spent))


def runaway_deletions(per_call_rows, calls):
    """A synthetic agent whose loop deletes per_call_rows rows on each of `calls` calls."""
    return [(f"delete#{i}", {"rows": per_call_rows, "customers": 1}) for i in range(calls)]


def demo():
    budget = ChangeBudget(limits={"rows": 500, "customers": 50})
    res = run_agent(budget, runaway_deletions(per_call_rows=120, calls=20), auto_approve=True)
    print("runaway halted:", res.halted, "committed:", res.committed, "spent:", res.spent)
    return res


if __name__ == "__main__":
    demo()
