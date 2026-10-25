"""A producer gate for agent-proposed events entering an existing event schema.

Author: Sandeep Belgavi. Standard library only; synthetic orders and proposals; no model or broker.

Flow: the agent proposes the data of an OrderAdjusted event (in production, via structured output),
`gate` validates it against the registered schema AND the order being handled, `publish` builds the
CloudEvents-style envelope in code and either appends it to the sink or writes the proposal to a
quarantine list. There is no retry loop.
"""
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

SCHEMA_ID = 'https://schemas.example.com/orders/OrderAdjusted/3'
REGISTERED_SCHEMA = {            # version 3 of the registered schema (JSON Schema 2020-12 subset)
    'type': 'object',
    'required': ['order_id', 'amount', 'currency', 'reason_code'],
    'additionalProperties': False,
    'properties': {
        'order_id': {'type': 'string', 'pattern': '^[0-9]{4,10}$'},
        'amount': {'type': 'string', 'pattern': '^[0-9]+\\.[0-9]{2}$'},
        'currency': {'type': 'string', 'enum': ['EUR', 'USD', 'INR']},
        'reason_code': {'type': 'string', 'enum': ['late_delivery', 'damaged_item', 'price_match']},
        'note': {'type': 'string', 'maxLength': 280},
    },
}
# Keywords a provider's structured-output mode may not enforce; each needs a gate check.
NOT_ENFORCED_BY_PROVIDER = {'pattern', 'maxLength'}


def structured_output_schema(registered=REGISTERED_SCHEMA):
    """Derive the schema sent to the model from the registered one, and list what the gate must re-check."""
    sent = json.loads(json.dumps(registered))
    stripped = []
    for name, prop in sent['properties'].items():
        for kw in sorted(NOT_ENFORCED_BY_PROVIDER & prop.keys()):
            stripped.append('%s.%s' % (name, kw))
            del prop[kw]
    return sent, sorted(stripped)


def _schema_problems(data, schema=REGISTERED_SCHEMA):
    import re
    problems = []
    if not isinstance(data, dict):
        return ['proposal is not an object']
    missing = [k for k in schema['required'] if k not in data]
    if missing:
        problems.append('missing fields: %s' % missing)
    extra = sorted(set(data) - set(schema['properties']))
    if extra and schema.get('additionalProperties') is False:
        problems.append('unexpected fields: %s' % extra)
    for name, rule in schema['properties'].items():
        if name not in data:
            continue
        v = data[name]
        if rule.get('type') == 'string' and not isinstance(v, str):
            problems.append('%s must be a string' % name)
            continue
        if 'enum' in rule and v not in rule['enum']:
            problems.append('%s not in the registered enum' % name)
        if 'pattern' in rule and not re.search(rule['pattern'], v):
            problems.append('%s does not match %s' % (name, rule['pattern']))
        if 'maxLength' in rule and len(v) > rule['maxLength']:
            problems.append('%s longer than %d' % (name, rule['maxLength']))
    return problems


def gate(proposal, order):
    """Return (ok, problems): full schema validation, then business rules against the order handled."""
    problems = _schema_problems(proposal)
    if problems:
        return False, problems
    if proposal['order_id'] != order['id']:
        problems.append('order_id does not match the order being handled')
    if proposal['currency'] != order['currency']:
        problems.append('currency differs from the order currency')
    try:
        amount = Decimal(proposal['amount'])
    except InvalidOperation:
        return False, problems + ['amount is not a decimal']
    if not (Decimal('0') < amount <= Decimal(order['total'])):
        problems.append('amount must be positive and at most the order total')
    return not problems, problems


def envelope(data, producer, now=None, event_id=None):
    """CloudEvents 1.0 attributes are set in code, never by the model."""
    return {
        'specversion': '1.0',
        'id': event_id or str(uuid.uuid4()),
        'source': 'urn:agent:%s' % producer['name'],
        'type': 'com.example.orders.OrderAdjusted',
        'time': (now or datetime.now(timezone.utc)).isoformat(),
        'dataschema': SCHEMA_ID,
        'datacontenttype': 'application/json',
        'producerversion': producer['version'],     # extension attribute: model + prompt release
        'data': data,
    }


def publish(proposal, order, producer, sink, quarantine, now=None, event_id=None):
    ok, problems = gate(proposal, order)
    if ok:
        sink.append(envelope(proposal, producer, now, event_id))
        return 'published', []
    quarantine.append({'proposal': proposal, 'order_id': order['id'], 'problems': problems,
                       'producer': producer, 'schema': SCHEMA_ID})
    return 'quarantined', problems


def demo(path='fixtures/proposals.json'):
    with open(path, encoding='utf-8') as f:
        fx = json.load(f)
    sink, quarantine = [], []
    for prop in fx['proposals']:
        outcome, problems = publish(prop, fx['order'], fx['producer'], sink, quarantine)
        print('%-11s %s %s' % (outcome, json.dumps(prop), problems))
    sent, stripped = structured_output_schema()
    print('published=%d quarantined=%d; keywords the gate re-checks: %s' % (len(sink), len(quarantine), stripped))


if __name__ == '__main__':
    demo()
