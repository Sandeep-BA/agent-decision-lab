"""Tests for graphql_operation_tools. Author: Sandeep Belgavi. Run: python -m unittest -v"""
import json, pathlib, unittest
from operation_tools import OPERATIONS, RunBudget, call_operation, null_prefix, to_tool_result

R = json.loads((pathlib.Path(__file__).resolve().parent / 'responses.json').read_text(encoding='utf-8'))
SENT = []


def transport(name):
    def send(document, variables):
        SENT.append(document)
        return R[name]
    return send


class GatewayTest(unittest.TestCase):
    def setUp(self):
        SENT.clear()

    def test_only_registered_documents_are_sent(self):
        call_operation('order_status_v1', {'id': 'BK-40211'}, RunBudget(10), transport('complete'))
        self.assertEqual(SENT, [OPERATIONS['order_status_v1'].document])
        r = call_operation('ad_hoc', {'query': '{ __schema { types { name } } }'}, RunBudget(10), transport('complete'))
        self.assertEqual(r['code'], 'unknown_operation')
        self.assertEqual(len(SENT), 1)

    def test_variables_are_checked_before_anything_is_spent(self):
        b = RunBudget(100)
        for bad in ({'id': 'bk-40211'}, {'id': 40211}, {}, {'id': 'BK-40211', 'extra': 1}):
            self.assertEqual(call_operation('order_status_v1', bad, b, transport('complete'))['code'], 'bad_variables')
        self.assertEqual(b.spent, 0)
        r = call_operation('customer_orders_v1', {'customer': 'CUS-1042', 'first': 26}, b, transport('complete'))
        self.assertEqual(r['code'], 'bad_variables')

    def test_budget_is_per_run_and_refusal_is_typed(self):
        b = RunBudget(300)
        self.assertEqual(call_operation('customer_orders_v1', {'customer': 'CUS-1042', 'first': 10}, b, transport('complete'))['status'], 'ok')
        r = call_operation('customer_orders_v1', {'customer': 'CUS-1042', 'first': 25}, b, transport('complete'))
        self.assertEqual((r['code'], b.spent), ('budget_exceeded', 211))
        self.assertIn('89 of 300', r['message'])


class PartialResultTest(unittest.TestCase):
    def test_failed_field_is_marked_unavailable_not_empty(self):
        r = to_tool_result(R['shipment_failed'])
        self.assertEqual(r['status'], 'partial')
        self.assertEqual(r['unavailable'], {'order.shipment': 'carrier service timed out'})

    def test_non_null_error_points_at_the_nullable_parent(self):
        self.assertEqual(null_prefix(R['order_null_propagated']['data'], ['order', 'lines', 0, 'title']), ['order'])
        self.assertEqual(to_tool_result(R['order_null_propagated'])['unavailable'], {'order': 'inventory service unavailable'})

    def test_request_error_has_no_data(self):
        r = to_tool_result(R['request_error'])
        self.assertEqual(r['status'], 'failed')
        self.assertIn('does not exist', r['note'])

    def test_complete_response(self):
        self.assertEqual(to_tool_result(R['complete'])['status'], 'ok')


if __name__ == '__main__':
    unittest.main()
