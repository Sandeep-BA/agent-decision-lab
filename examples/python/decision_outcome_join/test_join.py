# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import unittest
from join import generate, join, run


class JoinTest(unittest.TestCase):
    def setUp(self):
        self.r = run()

    def test_counts_after_every_window_closed(self):
        f = self.r['final']
        self.assertEqual((f['agent'], f['all_person_cases'], f['eligible_holdout']), ((41, 479), (101, 521), (9, 116)))

    def test_naive_comparison_looks_like_a_large_win(self):
        self.assertEqual(self.r['naive_diff'], [-10.8, -15.0, -6.6])

    def test_holdout_comparison_cannot_exclude_zero(self):
        d, lo, hi = self.r['holdout_diff']
        self.assertEqual(d, 0.8)
        self.assertLess(lo, 0)
        self.assertGreater(hi, 0)

    def test_reading_before_windows_close_undercounts(self):
        self.assertEqual(self.r['early_unclosed']['agent'], (37, 479))

    def test_reopen_after_the_window_is_not_attributed(self):
        rows = join([{'case_id': 'CASE-1', 'decided_day': 0, 'arm': 'agent', 'eligible': True}],
                    [{'case_id': 'CASE-1', 'reopened_day': 8}], as_of_day=30)
        self.assertEqual((rows[0]['window_closed'], rows[0]['reopened']), (True, False))

    def test_generator_is_deterministic(self):
        self.assertEqual(generate()[0][:3], generate()[0][:3])


if __name__ == '__main__':
    unittest.main()
