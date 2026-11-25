"""Expose only the tools the current workflow state allows. Author: Sandeep Belgavi.

Synthetic help-desk refund workflow for Belgavi's Book Store. The tool list offered to a
model is derived from persisted case state on every turn, and the executor re-checks the
same table at call time, because the state can change between listing and calling.
No model or remote service is contacted.
"""
from dataclasses import dataclass, field
import json

TOOLS = {
    "lookup_order": {"effect": "read"},
    "request_receipt_photo": {"effect": "message"},
    "mark_verified": {"effect": "write"},
    "issue_refund": {"effect": "money"},
    "close_case": {"effect": "write"},
}

# state -> tools the agent may see and call in that state (closed allowlist)
ALLOWED = {
    "awaiting_verification": {"lookup_order", "request_receipt_photo", "mark_verified"},
    "verified": {"lookup_order", "issue_refund"},
    "refunded": {"lookup_order", "close_case"},
    "closed": set(),
}

# tool -> next state when the call succeeds (None means no transition)
TRANSITIONS = {
    "mark_verified": "verified",
    "issue_refund": "refunded",
    "close_case": "closed",
}


@dataclass
class Case:
    case_id: str
    state: str
    revision: int = 0
    log: list = field(default_factory=list)


def visible_tools(case):
    """Tool definitions for this turn: a pure function of persisted state."""
    if case.state not in ALLOWED:
        raise ValueError(f"unknown state {case.state!r}")
    return sorted(ALLOWED[case.state])


def execute(case, tool, listed_revision):
    """Re-check authority at execution time; never trust the earlier listing alone."""
    if tool not in TOOLS:
        return "rejected_unknown_tool"
    if tool not in ALLOWED.get(case.state, set()):
        return "rejected_not_allowed_in_state"
    if TOOLS[tool]["effect"] in {"write", "money"} and listed_revision != case.revision:
        return "rejected_stale_listing"
    case.log.append((case.revision, case.state, tool))
    nxt = TRANSITIONS.get(tool)
    if nxt:
        case.state = nxt
        case.revision += 1
    return "applied"


def demo():
    case = Case("CASE-4107", "awaiting_verification")
    trace = []
    listed = visible_tools(case)
    trace.append({"turn": 1, "state": case.state, "visible": listed})
    # A model asks for a refund before verification: not visible, and rejected if attempted.
    trace.append({"turn": 1, "call": "issue_refund", "result": execute(case, "issue_refund", case.revision)})
    trace.append({"turn": 1, "call": "mark_verified", "result": execute(case, "mark_verified", 0)})
    listed_rev = case.revision
    trace.append({"turn": 2, "state": case.state, "visible": visible_tools(case)})
    # A second worker refunds first; our listing (revision 1) is now stale.
    other = execute(case, "issue_refund", listed_rev)
    trace.append({"turn": 2, "call": "issue_refund (other worker)", "result": other})
    trace.append({"turn": 2, "call": "issue_refund (this worker, stale)", "result": execute(case, "issue_refund", listed_rev)})
    trace.append({"turn": 3, "state": case.state, "visible": visible_tools(case)})
    return {"final_state": case.state, "revision": case.revision, "trace": trace}


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
