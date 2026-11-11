"""Maker-checker rules when agents can request, edit and relay approvals. Author: Sandeep Belgavi.

Standard library only. Principals are resolved to the accountable person behind them before
any rule runs, so an agent never counts as a separate person.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Principal:
    id: str
    kind: str                      # 'human' | 'agent' | 'service'
    on_behalf_of: str | None = None  # the human an agent or service acts for
    roles: frozenset = frozenset()


@dataclass
class Request:
    case: str
    amount: int                    # refund amount in whole currency units
    requested_by: Principal
    edits: list = field(default_factory=list)   # principals who changed the payload after creation


def accountable(p: Principal) -> str | None:
    """The human answerable for an action. Agents and services must name one."""
    return p.id if p.kind == 'human' else p.on_behalf_of


def decide(req: Request, approver: Principal, limits: dict) -> tuple[bool, str]:
    """Return (allowed, reason). Rules run in a fixed order; the first failure wins."""
    if approver.kind != 'human':
        return False, 'approver must be a person, not an agent or service'
    if 'refund_approver' not in approver.roles:
        return False, 'approver lacks the refund_approver role'
    if req.amount > limits.get(approver.id, 0):
        return False, f'amount {req.amount} exceeds approver limit {limits.get(approver.id, 0)}'
    maker = accountable(req.requested_by)
    if maker is None:
        return False, 'requester has no accountable person'
    if maker == approver.id:
        return False, 'approver is the accountable requester'
    for editor in req.edits:
        who = accountable(editor)
        if who is None:
            return False, 'an editor has no accountable person'
        if who == approver.id:
            return False, 'approver edited the payload, so they are also a maker'
    return True, f'approved: maker {maker}, checker {approver.id}'


GEETHA = Principal('geetha', 'human', roles=frozenset({'refund_approver'}))
JENYA = Principal('jenya', 'human', roles=frozenset({'refund_approver'}))
TANISHKA = Principal('tanishka', 'human')
AGENT_FOR_TANISHKA = Principal('desk-agent-7', 'agent', on_behalf_of='tanishka')
AGENT_FOR_GEETHA = Principal('desk-agent-9', 'agent', on_behalf_of='geetha')
ORPHAN_AGENT = Principal('batch-agent', 'agent')
LIMITS = {'geetha': 500, 'jenya': 100}

CASES = [
    ('agent drafts for Tanishka, Geetha approves', Request('CASE-5101', 120, AGENT_FOR_TANISHKA), GEETHA),
    ('agent drafts for Geetha, Geetha approves', Request('CASE-5102', 120, AGENT_FOR_GEETHA), GEETHA),
    ('agent drafts for Tanishka, Geetha edits then approves', Request('CASE-5103', 120, AGENT_FOR_TANISHKA, [AGENT_FOR_GEETHA]), GEETHA),
    ('agent drafts for Tanishka, agent for Geetha approves', Request('CASE-5104', 120, AGENT_FOR_TANISHKA), AGENT_FOR_GEETHA),
    ('agent with no owner drafts', Request('CASE-5105', 40, ORPHAN_AGENT), JENYA),
    ('Jenya approves above her limit', Request('CASE-5106', 120, AGENT_FOR_TANISHKA), JENYA),
]

if __name__ == '__main__':
    for label, req, approver in CASES:
        ok, why = decide(req, approver, LIMITS)
        print(f'{req.case} {label}: {"ALLOW" if ok else "DENY"} - {why}')
