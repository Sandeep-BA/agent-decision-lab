"""Replay a few agent tool calls through the operation gateway. Author: Sandeep Belgavi."""
import json, pathlib
from operation_tools import RunBudget, call_operation

RESPONSES = json.loads((pathlib.Path(__file__).resolve().parent / 'responses.json').read_text(encoding='utf-8'))


def fake(name):
    return lambda document, variables: RESPONSES[name]


if __name__ == '__main__':
    budget = RunBudget(limit=300)
    steps = [
        ('order_status_v1', {'id': 'BK-40211'}, 'shipment_failed'),
        ('order_status_v1', {'id': 'BK-40211'}, 'order_null_propagated'),
        ('customer_orders_v1', {'customer': 'CUS-1042', 'first': 10}, 'complete'),
        ('customer_orders_v1', {'customer': 'CUS-1042', 'first': 25}, 'complete'),
        ('ad_hoc', {'query': '{ customers { orders { lines { sku } } } }'}, 'complete'),
        ('order_status_v1', {'id': 'bk-40211'}, 'complete'),
    ]
    for op_id, variables, response in steps:
        result = call_operation(op_id, variables, budget, fake(response))
        print('%-18s %-30s -> %s' % (op_id, json.dumps(variables)[:30], json.dumps({k: v for k, v in result.items() if k != 'data'})))
    print('budget spent %d of %d: %s' % (budget.spent, budget.limit, budget.calls))
