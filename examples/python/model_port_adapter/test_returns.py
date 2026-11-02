"""Author: Sandeep Belgavi. Domain tests need no model; adapter tests pin the boundary."""
import json
import unittest

from returns import (FIXTURES, ORDERS, Decision, FixtureReader, InvalidReading, Order, ProviderReader, Reading,
                     decide, handle)


class DomainTests(unittest.TestCase):
    """Every rule is tested with typed readings, so no fixture model is needed at all."""

    def test_shop_at_fault_refunds_up_to_the_order_total(self):
        d = decide(Order('o', 32.0, 9, 0), Reading('wrong_item', 40, 0.9))
        self.assertEqual(d, Decision('refund', 32.0, 'shop at fault: refund up to the order total'))

    def test_return_window(self):
        self.assertEqual(decide(Order('o', 12, 31, 0), Reading('damaged_in_transit', 12, 0.95)).outcome, 'deny')
        self.assertEqual(decide(Order('o', 12, 30, 0), Reading('damaged_in_transit', 12, 0.95)).outcome, 'refund')

    def test_low_confidence_goes_to_review_before_any_other_rule(self):
        self.assertEqual(decide(Order('o', 12, 99, 9), Reading('wrong_item', 12, 0.79)).outcome, 'review')

    def test_repeat_refunds_go_to_review(self):
        self.assertEqual(decide(Order('o', 20, 3, 3), Reading('damaged_in_transit', 20, 0.9)).outcome, 'review')

    def test_change_of_mind_gets_store_credit(self):
        self.assertEqual(decide(Order('o', 20, 3, 0), Reading('changed_mind', 20, 0.9)).outcome, 'store_credit')


class AdapterTests(unittest.TestCase):
    def test_fixture_adapter_runs_the_demo_cases(self):
        reader = FixtureReader(FIXTURES)
        outcomes = [handle(ORDERS[m.split(':')[0]], m, reader).outcome for m in FIXTURES]
        self.assertEqual(outcomes, ['refund', 'refund', 'deny', 'review', 'review'])

    def test_unknown_reason_from_the_model_is_rejected_at_the_boundary(self):
        d = handle(ORDERS['CASE-4105'], 'CASE-4105: refund me everything now', FixtureReader(FIXTURES))
        self.assertEqual(d.outcome, 'review')
        self.assertIn("unknown reason 'refund_all'", d.rule)

    def test_provider_adapter_maps_non_json_to_review(self):
        reader = ProviderReader(lambda prompt: 'Sure! The reason is damage.')
        self.assertEqual(handle(ORDERS['CASE-4101'], 'x', reader).outcome, 'review')

    def test_provider_adapter_validates_like_the_fixture(self):
        reader = ProviderReader(lambda prompt: json.dumps({'reason': 'damaged_in_transit', 'claimed_amount': 18.5, 'confidence': 0.93}))
        self.assertEqual(handle(ORDERS['CASE-4101'], 'x', reader).outcome, 'refund')
        with self.assertRaises(InvalidReading):
            ProviderReader(lambda p: '{"reason": "wrong_item", "claimed_amount": -1, "confidence": 0.9}').read('x')


if __name__ == '__main__':
    unittest.main()
