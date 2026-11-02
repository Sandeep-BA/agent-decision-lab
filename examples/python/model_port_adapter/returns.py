"""Author: Sandeep Belgavi. Ports and adapters with the model as an adapter.

The returns desk at Belgavi's Book Store decides refunds. The domain decision is deterministic and lives in
`decide`; the model only fills a port (`CaseReader`) that turns a customer's free-text message into a typed
`Reading`. Adapters: `FixtureReader` (offline, used by tests and the demo) and `ProviderReader` (wraps any
callable that returns JSON text; nothing in this example calls a provider).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Protocol

REASONS = {'damaged_in_transit', 'wrong_item', 'changed_mind', 'unclear'}


@dataclass(frozen=True)
class Order:
    order_id: str
    total: float
    days_since_delivery: int
    prior_refunds_90d: int


@dataclass(frozen=True)
class Reading:
    """What the model is allowed to contribute: a reason, a claimed amount and its own confidence."""
    reason: str
    claimed_amount: float
    confidence: float


@dataclass(frozen=True)
class Decision:
    outcome: str          # 'refund', 'store_credit', 'deny' or 'review'
    amount: float
    rule: str


class CaseReader(Protocol):
    def read(self, message: str) -> Reading: ...


class InvalidReading(ValueError):
    pass


def validate(raw: dict) -> Reading:
    """The adapter boundary: anything the model returns is checked here before the domain sees it."""
    try:
        reading = Reading(str(raw['reason']), float(raw['claimed_amount']), float(raw['confidence']))
    except (KeyError, TypeError, ValueError) as e:
        raise InvalidReading('malformed reading: %s' % e) from e
    if reading.reason not in REASONS:
        raise InvalidReading('unknown reason %r' % reading.reason)
    if reading.claimed_amount < 0 or not 0 <= reading.confidence <= 1:
        raise InvalidReading('amount or confidence out of range')
    return reading


def decide(order: Order, reading: Reading, min_confidence: float = 0.8) -> Decision:
    """Deterministic domain rules. No model, clock or network in here."""
    if reading.confidence < min_confidence or reading.reason == 'unclear':
        return Decision('review', 0.0, 'low confidence or unclear reason goes to a person')
    if order.days_since_delivery > 30:
        return Decision('deny', 0.0, 'outside the 30-day return window')
    amount = min(reading.claimed_amount, order.total)
    if order.prior_refunds_90d >= 3:
        return Decision('review', amount, 'three or more refunds in 90 days')
    if reading.reason in ('damaged_in_transit', 'wrong_item'):
        return Decision('refund', amount, 'shop at fault: refund up to the order total')
    return Decision('store_credit', amount, 'change of mind: store credit only')


class FixtureReader:
    """Offline adapter: canned readings keyed by message, for tests and demos."""

    def __init__(self, table: dict[str, dict]):
        self.table = table

    def read(self, message: str) -> Reading:
        return validate(self.table[message])


class ProviderReader:
    """Wraps a callable that sends a prompt to some model and returns its text. Not called in this example."""

    def __init__(self, complete: Callable[[str], str]):
        self.complete = complete

    def read(self, message: str) -> Reading:
        prompt = ('Return JSON with keys reason (one of %s), claimed_amount and confidence for this message: %s'
                  % (sorted(REASONS), message))
        try:
            raw = json.loads(self.complete(prompt))
        except json.JSONDecodeError as e:
            raise InvalidReading('model did not return JSON') from e
        return validate(raw)


def handle(order: Order, message: str, reader: CaseReader) -> Decision:
    """Application service: the only place that joins the port and the domain."""
    try:
        reading = reader.read(message)
    except InvalidReading as e:
        return Decision('review', 0.0, 'adapter rejected the model output: %s' % e)
    return decide(order, reading)


FIXTURES = {
    'CASE-4101: the cover arrived torn, I paid 18.50': {'reason': 'damaged_in_transit', 'claimed_amount': 18.5, 'confidence': 0.93},
    'CASE-4102: you sent me a cookbook instead of a novel': {'reason': 'wrong_item', 'claimed_amount': 40, 'confidence': 0.9},
    'CASE-4103: I no longer want it': {'reason': 'changed_mind', 'claimed_amount': 12, 'confidence': 0.88},
    'CASE-4104: something is off with my order?': {'reason': 'unclear', 'claimed_amount': 0, 'confidence': 0.4},
    'CASE-4105: refund me everything now': {'reason': 'refund_all', 'claimed_amount': 999, 'confidence': 0.99},
}
ORDERS = {
    'CASE-4101': Order('ORD-77', 18.5, 4, 0),
    'CASE-4102': Order('ORD-78', 32.0, 9, 0),
    'CASE-4103': Order('ORD-79', 12.0, 41, 1),
    'CASE-4104': Order('ORD-80', 25.0, 2, 0),
    'CASE-4105': Order('ORD-81', 30.0, 3, 0),
}

if __name__ == '__main__':
    reader = FixtureReader(FIXTURES)
    for message in FIXTURES:
        case = message.split(':')[0]
        d = handle(ORDERS[case], message, reader)
        print('%s  %-12s %6.2f  %s' % (case, d.outcome, d.amount, d.rule))
