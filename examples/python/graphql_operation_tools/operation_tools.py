"""Expose registered GraphQL operations to an agent as tools, with a per-run cost budget and honest
partial results.

Author: Sandeep Belgavi.

The agent never sends a GraphQL document. It picks an operation id and supplies variables; the
gateway checks the variables, estimates the cost from the operation's declared list sizes, charges
the run's budget, sends the persisted document, and turns the response into a tool result. A field
that is null because a resolver failed is reported as unavailable with the error message, so the
model cannot read it as "no data".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


class ToolError(Exception):
    """A typed refusal the agent can act on."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message

    def as_result(self):
        return {'status': 'refused', 'code': self.code, 'message': self.message}


@dataclass(frozen=True)
class Operation:
    op_id: str
    document: str
    variables: dict            # name -> (python type, regex or None, max or None)
    cost: callable             # variables -> estimated cost
    description: str


ORDER = (str, r'^BK-[0-9]{5}$', None)
OPERATIONS = {op.op_id: op for op in (
    Operation('order_status_v1',
              'query OrderStatus($id: ID!) { order(id: $id) { id status placedAt '
              'shipment { carrier lastEvent } lines { sku title quantity } } }',
              {'id': ORDER}, lambda v: 3, 'Status, shipment and lines of one order.'),
    Operation('customer_orders_v1',
              'query CustomerOrders($customer: ID!, $first: Int!) { customer(id: $customer) { '
              'orders(first: $first) { id status total lines(first: 20) { sku quantity } } } }',
              {'customer': (str, r'^CUS-[0-9]{4,8}$', None), 'first': (int, None, 25)},
              lambda v: 1 + v['first'] * (1 + 20), 'Recent orders of one customer, at most 25.'),
)}


@dataclass
class RunBudget:
    limit: int
    spent: int = 0
    calls: list = field(default_factory=list)

    def charge(self, op_id, cost):
        if self.spent + cost > self.limit:
            raise ToolError('budget_exceeded', 'This run has %d of %d cost units left; %s needs %d.'
                            % (self.limit - self.spent, self.limit, op_id, cost))
        self.spent += cost
        self.calls.append((op_id, cost))


def check_variables(op, variables):
    unknown = set(variables) - set(op.variables)
    if unknown:
        raise ToolError('bad_variables', 'Unknown variables: %s.' % ', '.join(sorted(unknown)))
    for name, (kind, pattern, maximum) in op.variables.items():
        if name not in variables:
            raise ToolError('bad_variables', 'Missing variable %s.' % name)
        value = variables[name]
        if not isinstance(value, kind) or isinstance(value, bool):
            raise ToolError('bad_variables', '%s must be %s.' % (name, kind.__name__))
        if pattern and not re.fullmatch(pattern, value):
            raise ToolError('bad_variables', '%s does not match %s.' % (name, pattern))
        if maximum is not None and not 1 <= value <= maximum:
            raise ToolError('bad_variables', '%s must be from 1 to %d.' % (name, maximum))


def call_operation(op_id, variables, budget, transport):
    """transport(document, variables) -> GraphQL response dict. Returns a tool result dict."""
    try:
        op = OPERATIONS.get(op_id)
        if op is None:
            raise ToolError('unknown_operation', 'Only registered operations can run: %s.' % ', '.join(sorted(OPERATIONS)))
        check_variables(op, variables)
        budget.charge(op_id, op.cost(variables))
        response = transport(op.document, variables)
    except ToolError as refusal:
        return refusal.as_result()
    return to_tool_result(response)


def null_prefix(data, path):
    """The shortest prefix of an error path that is null in the data. A field error on a non-null field
    propagates to the nearest nullable parent, so that parent, not the leaf, is what is missing."""
    node = data
    for i, key in enumerate(path):
        try:
            node = node[key]
        except (KeyError, IndexError, TypeError):
            return path[:i + 1]
        if node is None:
            return path[:i + 1]
    return path


def to_tool_result(response):
    errors = response.get('errors') or []
    data = response.get('data')
    if data is None:
        return {'status': 'failed', 'errors': [e.get('message') for e in errors],
                'note': 'No data was returned. Do not tell the customer the record does not exist.'}
    unavailable = {}
    for e in errors:
        path = e.get('path')
        if path:
            unavailable['.'.join(str(p) for p in null_prefix(data, path))] = e.get('message')
    result = {'status': 'partial' if errors else 'ok', 'data': data}
    if unavailable:
        result['unavailable'] = unavailable
        result['note'] = ('Fields listed under unavailable are null because they failed to load, not because '
                          'they are empty. Say they are unavailable; do not infer their value.')
    return result
