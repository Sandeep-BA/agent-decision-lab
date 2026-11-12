"""Author: Sandeep Belgavi. The deterministic rule layer that checks refund proposals from an
agent at the fictional Belgavi's Book Store. Money is in integer minor units (paise)."""
from dataclasses import dataclass, field

APPROVAL_THRESHOLD = 500_000          # proposals above 5,000.00 need a person
REFUNDABLE = {"delivered", "returned"}


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    order_id: str
    amount: int                       # paise
    currency: str = "INR"


@dataclass
class Order:
    order_id: str
    total: int
    currency: str = "INR"
    status: str = "delivered"
    refunded: int = 0
    seen: set = field(default_factory=set)


def check(order: Order, p: Proposal) -> str:
    """Returns accept | needs-approval | reject:<reason> | duplicate, and records accepted refunds."""
    if p.proposal_id in order.seen:
        return "duplicate"
    if p.order_id != order.order_id:
        return "reject:wrong-order"
    if p.currency != order.currency:
        return "reject:currency"
    if order.status not in REFUNDABLE:
        return "reject:status"
    if p.amount <= 0:
        return "reject:non-positive"
    if p.amount > order.total - order.refunded:
        return "reject:exceeds-remaining"
    if p.amount > APPROVAL_THRESHOLD:
        return "needs-approval"
    order.seen.add(p.proposal_id)
    order.refunded += p.amount
    return "accept"


def check_buggy(order: Order, p: Proposal) -> str:
    """The version that shipped first: compares against the order total, forgetting earlier refunds."""
    if p.proposal_id in order.seen:
        return "duplicate"
    if p.order_id != order.order_id or p.currency != order.currency or order.status not in REFUNDABLE or p.amount <= 0:
        return "reject:basic"
    if p.amount > order.total:
        return "reject:exceeds-total"
    if p.amount > APPROVAL_THRESHOLD:
        return "needs-approval"
    order.seen.add(p.proposal_id)
    order.refunded += p.amount
    return "accept"
