"""Enum values between an agent and an existing service: strict on write, tolerant on read.

Author: Sandeep Belgavi. Companion to "Enum Values Between Agents and Existing Services" (aicassindra.com).
Standard library only; the returns and order services are in-memory fakes.
"""
from dataclasses import dataclass

REASONS = {'damaged', 'wrong_item', 'not_as_described', 'changed_mind'}
ALIASES = {'damaged_in_transit': 'damaged', 'arrived_damaged': 'damaged', 'incorrect_item': 'wrong_item'}
STATUSES = {'placed': 'processing', 'packed': 'processing', 'shipped': 'in_transit', 'delivered': 'delivered'}


class UnknownValue(Exception):
    def __init__(self, field, value, allowed):
        super().__init__(f'{field}={value!r} is not one of {sorted(allowed)}')
        self.payload = {'error': 'unknown_enum_value', 'field': field, 'value': value, 'allowed': sorted(allowed)}


def canonical_reason(value):
    v = ALIASES.get(value.strip().lower(), value.strip().lower())
    if v not in REASONS:
        raise UnknownValue('return_reason', value, REASONS)
    return v


def legacy_reason(value):
    """The old compatibility layer: lowercases and silently maps anything unknown to the default."""
    v = value.strip().lower()
    return v if v in REASONS else 'changed_mind'


def create_return(order_id, reason):
    """Write tool: returns a result the agent can act on instead of raising into the model loop."""
    try:
        return {'ok': True, 'order_id': order_id, 'reason': canonical_reason(reason)}
    except UnknownValue as e:
        return {'ok': False, **e.payload}


@dataclass(frozen=True)
class OrderStatus:
    value: str        # canonical value, or 'UNKNOWN'
    raw: str          # what the service sent
    category: str     # coarse category the agent can always explain
    label: str        # human-readable text the agent may quote


def read_status(payload, known=STATUSES):
    """Read tool: never throws on a value it has not seen; keeps the raw value and the service's category."""
    raw = payload['status']
    if raw in known:
        return OrderStatus(raw, raw, known[raw], payload.get('label', raw))
    return OrderStatus('UNKNOWN', raw, payload.get('status_category', 'unknown'), payload.get('label', raw))


def strict_status(payload):
    """What a Java-style enum valueOf does: throws on an unseen name."""
    raw = payload['status']
    if raw not in STATUSES:
        raise ValueError(f'No enum constant OrderStatus.{raw}')
    return raw


if __name__ == '__main__':
    import json, pathlib
    here = pathlib.Path(__file__).resolve().parent
    for value in ('Damaged', 'damaged_in_transit', 'DAMAGED', 'water_damage'):
        print(json.dumps({'sent': value, 'legacy': legacy_reason(value), 'strict': create_return('BK-301', value)}))
    payload = json.loads((here / 'fixtures' / 'order_partially_shipped.json').read_text(encoding='utf-8'))
    print(json.dumps(read_status(payload).__dict__))
