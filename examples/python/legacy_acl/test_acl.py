"""Author: Sandeep Belgavi. Tests for the anti-corruption layer example."""
import unittest

from acl import FakeBackOffice, RefundRejected, ReturnsLayer, UnknownCode, demo, naive_status, to_view


def office():
    bo = FakeBackOffice()
    bo.add('CASE-1', 'R', 2499, 2499, era='B')
    bo.add('CASE-2', 'R', 1500, 0, era='A')
    bo.add('CASE-3', 'O', 3000, 0)
    bo.add('CASE-4', 'H', 1200, 0)
    bo.add('CASE-5', 'X', 800, 1600, method='SC')
    return bo


class TranslationTests(unittest.TestCase):
    def test_r_depends_on_the_era_flag(self):
        layer = ReturnsLayer(office())
        self.assertEqual(layer.get_return('CASE-1').status, 'refunded')
        self.assertEqual(layer.get_return('CASE-2').status, 'rejected')

    def test_the_naive_reading_gets_the_refunded_case_wrong(self):
        hdr, _ = office().read('CASE-1')
        self.assertEqual(naive_status(hdr), 'rejected')

    def test_store_credit_points_become_pence(self):
        self.assertEqual(ReturnsLayer(office()).get_return('CASE-5').refunded_pence, 800)

    def test_unknown_codes_are_errors_not_defaults(self):
        with self.assertRaises(UnknownCode):
            to_view(dict(CASE='C', STS='Q', PAID_AMT=1, RFD_AMT=0, RFD_MTH='CARD'), 'B')

    def test_legacy_errors_become_typed_results(self):
        self.assertEqual(ReturnsLayer(office()).get_return('CASE-404'), dict(error='not_found', retryable=False))


class RefundTests(unittest.TestCase):
    def test_timeout_after_recording_then_retry_posts_once(self):
        bo = office()
        layer = ReturnsLayer(bo)
        bo.fail_post_after_record = True
        with self.assertRaises(TimeoutError):
            layer.refund('CASE-3', 1000, key='k1')
        again = layer.refund('CASE-3', 1000, key='k1')
        self.assertEqual(again['id'], 'P1')
        self.assertEqual(len(bo.postings), 1)
        self.assertEqual(bo.holds, {})                 # the hold is always released

    def test_invariants_are_enforced_before_any_legacy_call(self):
        bo = office()
        layer = ReturnsLayer(bo)
        for case, amount in (('CASE-4', 100), ('CASE-3', 3001), ('CASE-3', 0), ('CASE-1', 1)):
            with self.assertRaises(RefundRejected):
                layer.refund(case, amount, key='x-%s-%d' % (case, amount))
        self.assertEqual(bo.postings, [])
        self.assertEqual(bo.next_hold, 1)              # nothing was even reserved

    def test_partial_refunds_add_up_to_the_paid_amount_and_no_more(self):
        bo = office()
        layer = ReturnsLayer(bo)
        layer.refund('CASE-3', 2000, key='a')
        layer.refund('CASE-3', 1000, key='b')
        with self.assertRaises(RefundRejected):
            layer.refund('CASE-3', 1, key='c')

    def test_demo_output_matches_the_readme(self):
        d = dict(demo())
        self.assertEqual(d['naive_7001'], 'rejected')
        self.assertEqual(d['layer_7001'], 'refunded')
        self.assertEqual(d['postings_for_7003'], 1)
        self.assertEqual(d['rejected_CASE-7003'], 'refund would exceed the amount paid')


if __name__ == '__main__':
    unittest.main()
