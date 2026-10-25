"""Author: Sandeep Belgavi. Tests for the agent event producer gate."""
import json
import os
import unittest
from datetime import datetime, timezone

import producer

HERE = os.path.dirname(os.path.abspath(__file__))


class GateTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(HERE, 'fixtures', 'proposals.json'), encoding='utf-8') as f:
            self.fx = json.load(f)
        self.order, self.props = self.fx['order'], self.fx['proposals']

    def run_all(self):
        sink, quarantine = [], []
        outcomes = [producer.publish(p, self.order, self.fx['producer'], sink, quarantine)[0] for p in self.props]
        return outcomes, sink, quarantine

    def test_worked_example_outcomes(self):
        outcomes, sink, quarantine = self.run_all()
        self.assertEqual(outcomes, ['published', 'quarantined', 'quarantined', 'quarantined'])
        self.assertEqual(len(sink), 1)
        self.assertEqual(len(quarantine), 3)

    def test_each_rejection_names_its_rule(self):
        _, _, q = self.run_all()
        self.assertIn('amount must be positive and at most the order total', q[0]['problems'])
        self.assertIn('currency differs from the order currency', q[1]['problems'])
        self.assertIn('order_id does not match the order being handled', q[2]['problems'])

    def test_schema_violations_are_caught_before_business_rules(self):
        ok, problems = producer.gate({'order_id': '7731', 'amount': '15', 'currency': 'EUR',
                                      'reason_code': 'goodwill', 'extra': 1}, self.order)
        self.assertFalse(ok)
        joined = ' | '.join(problems)
        self.assertIn('unexpected fields', joined)
        self.assertIn('reason_code not in the registered enum', joined)
        self.assertIn('amount does not match', joined)

    def test_envelope_is_built_in_code(self):
        now = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
        sink, q = [], []
        producer.publish(self.props[0], self.order, self.fx['producer'], sink, q, now=now, event_id='evt-1')
        ev = sink[0]
        self.assertEqual(ev['specversion'], '1.0')
        self.assertEqual(ev['type'], 'com.example.orders.OrderAdjusted')
        self.assertEqual(ev['dataschema'], producer.SCHEMA_ID)
        self.assertEqual(ev['source'], 'urn:agent:support-agent')
        self.assertEqual(ev['time'], '2026-10-25T12:00:00+00:00')
        self.assertEqual(ev['data'], self.props[0])

    def test_structured_output_schema_lists_what_the_gate_rechecks(self):
        sent, stripped = producer.structured_output_schema()
        self.assertEqual(stripped, ['amount.pattern', 'note.maxLength', 'order_id.pattern'])
        self.assertNotIn('pattern', sent['properties']['amount'])
        self.assertIn('pattern', producer.REGISTERED_SCHEMA['properties']['amount'])

    def test_no_retry_loop(self):
        calls = {'n': 0}
        original = producer.gate
        def counting(p, o):
            calls['n'] += 1
            return original(p, o)
        producer.gate = counting
        try:
            producer.publish(self.props[1], self.order, self.fx['producer'], [], [])
        finally:
            producer.gate = original
        self.assertEqual(calls['n'], 1)


if __name__ == '__main__':
    unittest.main()
