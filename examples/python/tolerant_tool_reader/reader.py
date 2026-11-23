"""Tolerant reader between an order service and an agent tool. Author: Sandeep Belgavi.

The agent's order-lookup tool needs four things from the order service of the
fictional Belgavi's Book Store: the order id, its status, the total and the
currency. A strict mirror validates the whole provider payload and rejects any
field it does not know. A tolerant reader takes only what the tool uses, ignores
the rest, maps a status it does not recognise to an explicit "escalate" outcome
and fails loudly, with a field path, only when a consumed field is missing or
malformed. Both readers count drift so the change is visible without breaking
the agent. Standard library only; synthetic payloads.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import json

KNOWN_STATUSES = {'placed', 'shipped', 'delivered', 'returned', 'refunded'}
# Everything the strict mirror knows about version 1 of the payload.
V1_FIELDS = {'order_id', 'status', 'customer', 'items', 'total', 'created_at'}


class ContractViolation(Exception):
    """A field the tool consumes is missing or malformed."""

    def __init__(self, path: str, problem: str):
        super().__init__(f'{path}: {problem}')
        self.path = path
        self.problem = problem


@dataclass
class Drift:
    unknown_fields: dict[str, int] = field(default_factory=dict)
    unknown_statuses: dict[str, int] = field(default_factory=dict)

    def note_field(self, name: str) -> None:
        self.unknown_fields[name] = self.unknown_fields.get(name, 0) + 1

    def note_status(self, value: str) -> None:
        self.unknown_statuses[value] = self.unknown_statuses.get(value, 0) + 1


@dataclass(frozen=True)
class OrderView:
    """The only shape the agent ever sees."""
    order_id: str
    status: str          # one of KNOWN_STATUSES, or 'escalate'
    raw_status: str
    total: Decimal
    currency: str
    note: str = ''


def strict_read(payload: dict) -> OrderView:
    """Mirror of the full v1 schema: any unknown field or status is an error."""
    extra = sorted(set(payload) - V1_FIELDS)
    if extra:
        raise ContractViolation(extra[0], 'unknown field in strict schema')
    missing = sorted(V1_FIELDS - set(payload))
    if missing:
        raise ContractViolation(missing[0], 'missing field in strict schema')
    if payload['status'] not in KNOWN_STATUSES:
        raise ContractViolation('status', f'unknown value {payload["status"]!r}')
    try:
        total = Decimal(str(payload['total']['amount']))
    except InvalidOperation:
        raise ContractViolation('total.amount', 'not a decimal') from None
    return OrderView(payload['order_id'], payload['status'], payload['status'], total, payload['total']['currency'])


def _require(payload: dict, path: str):
    node = payload
    for part in path.split('.'):
        if not isinstance(node, dict) or part not in node:
            raise ContractViolation(path, 'missing consumed field')
        node = node[part]
    return node


def tolerant_read(payload: dict, drift: Drift) -> OrderView:
    """Read only consumed fields; record, never reject, what the tool does not use."""
    for name in sorted(set(payload) - V1_FIELDS):
        drift.note_field(name)
    order_id = _require(payload, 'order_id')
    if not isinstance(order_id, str) or not order_id:
        raise ContractViolation('order_id', 'must be a non-empty string')
    raw_status = _require(payload, 'status')
    if not isinstance(raw_status, str):
        raise ContractViolation('status', 'must be a string')
    amount_text = _require(payload, 'total.amount')
    currency = _require(payload, 'total.currency')
    try:
        total = Decimal(str(amount_text))
    except InvalidOperation:
        raise ContractViolation('total.amount', f'not a decimal: {amount_text!r}') from None
    if not (isinstance(currency, str) and len(currency) == 3 and currency.isupper()):
        raise ContractViolation('total.currency', f'not an ISO 4217 code: {currency!r}')
    if raw_status in KNOWN_STATUSES:
        return OrderView(order_id, raw_status, raw_status, total, currency)
    drift.note_status(raw_status)
    return OrderView(order_id, 'escalate', raw_status, total, currency,
                     note=f'status {raw_status!r} is not one the tool understands; route to a person')


V1 = {'order_id': 'ORD-7001', 'status': 'shipped', 'customer': {'name': 'Geetha'},
      'items': [{'isbn': '9780000000017', 'qty': 1}], 'total': {'amount': '24.50', 'currency': 'EUR'},
      'created_at': '2026-11-20T09:00:00Z'}
# v2: the service adds two fields and a new status. Nothing the tool uses changed.
V2 = dict(V1, order_id='ORD-7002', status='partially_shipped', gift_wrap=True, carrier_events=[{'at': '2026-11-21'}])
# v3: the service renames total to grand_total. A consumed field disappeared.
V3 = {k: v for k, v in V1.items() if k != 'total'} | {'order_id': 'ORD-7003', 'grand_total': {'amount': '24.50', 'currency': 'EUR'}}
V4 = dict(V1, order_id='ORD-7004', total={'amount': '24,50', 'currency': 'EUR'})

PAYLOADS = [('v1 unchanged', V1), ('v2 additive', V2), ('v3 renamed total', V3), ('v4 bad decimal', V4)]


def run() -> list[dict]:
    drift = Drift()
    rows = []
    for label, payload in PAYLOADS:
        row = {'payload': label}
        for name, reader in (('strict', strict_read), ('tolerant', lambda p: tolerant_read(p, drift))):
            try:
                view = reader(payload)
                row[name] = f'ok status={view.status}' + (f' (raw {view.raw_status})' if view.status == 'escalate' else '')
            except ContractViolation as e:
                row[name] = f'violation {e.path}: {e.problem}'
        rows.append(row)
    rows.append({'drift': {'unknown_fields': drift.unknown_fields, 'unknown_statuses': drift.unknown_statuses}})
    return rows


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
