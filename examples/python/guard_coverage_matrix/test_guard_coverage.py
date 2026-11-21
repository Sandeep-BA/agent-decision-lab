# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import unittest
from guard_coverage import FIXTURES, analyse, route


class GuardCoverageTest(unittest.TestCase):
    def test_complete_partitions_all_eight(self):
        r = analyse(FIXTURES['complete'])
        self.assertEqual((r['gaps'], r['overlaps'], r['strict_accepts']), (0, 0, True))
        self.assertEqual(len(r['rows']), 8)
        self.assertEqual(r['never_chosen'], [])

    def test_gap_is_the_unconfident_small_verified_request(self):
        r = analyse(FIXTURES['gap'])
        self.assertEqual((r['gaps'], r['overlaps'], r['strict_accepts']), (1, 0, False))
        gap = [x for x in r['rows'] if x['kind'] == 'gap'][0]
        self.assertEqual(gap['facts'], 'verified=T, over_limit=F, confident=F')

    def test_overlap_priority_auto_refunds_unverified_customer(self):
        risky = {'verified': False, 'over_limit': False, 'confident': True}
        self.assertEqual(route(FIXTURES['overlap'], risky, mode='priority'), 'auto_refund')
        self.assertEqual(route(FIXTURES['overlap'], risky, mode='priority', order='reversed'), 'verify_identity')

    def test_strict_refuses_overlap_before_any_request(self):
        safe = {'verified': True, 'over_limit': True, 'confident': True}
        with self.assertRaisesRegex(ValueError, '1 overlap'):
            route(FIXTURES['overlap'], safe, mode='strict')

    def test_fallback_closes_gaps_but_not_overlaps(self):
        self.assertTrue(analyse(FIXTURES['gap'], fallback=True)['strict_accepts'])
        self.assertFalse(analyse(FIXTURES['overlap'], fallback=True)['strict_accepts'])
        lonely = {'verified': True, 'over_limit': False, 'confident': False}
        self.assertEqual(route(FIXTURES['gap'], lonely, fallback=True), 'escalate_to_person')

    def test_priority_without_fallback_cannot_route_gap(self):
        lonely = {'verified': True, 'over_limit': False, 'confident': False}
        with self.assertRaises(LookupError):
            route(FIXTURES['gap'], lonely, mode='priority')


if __name__ == '__main__':
    unittest.main()
