# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import unittest
from recall_ties import CASES, DIST, exact_topk, kth_distance, report, tie_aware_recall

EXPECTED = {
    'exact order': (1.0, 1.0, 1.0),
    'other boundary tie': (0.667, 1.0, 1.0),
    'misses a closer item': (0.333, 1.0, 0.667),
    'duplicate': (0.667, 1.0, 0.667),
    'one wrong item': (0.667, 0.667, 0.667),
}


class RecallTiesTest(unittest.TestCase):
    def test_boundary_has_three_way_tie(self):
        self.assertEqual(kth_distance(DIST, 3), 0.30)
        self.assertEqual(sum(1 for d in DIST.values() if d == 0.30), 3)

    def test_table(self):
        for name, returned in CASES:
            self.assertEqual(report(name, returned)[1:], EXPECTED[name], name)

    def test_k_without_tie_agrees_with_id_recall(self):
        returned = ['KB-101 returns window', 'KB-103 damaged book']
        self.assertEqual(exact_topk(DIST, 2), ['KB-101 returns window', 'KB-102 refund to card'])
        self.assertEqual(tie_aware_recall(returned, DIST, 2), 0.5)

    def test_order_inside_the_result_does_not_matter(self):
        a = ['KB-105 late delivery refund', 'KB-102 refund to card', 'KB-101 returns window']
        self.assertEqual(tie_aware_recall(a, DIST, 3), 1.0)


if __name__ == '__main__':
    unittest.main()
