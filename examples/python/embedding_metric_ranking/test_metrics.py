"""Tests for the metric comparison. Author: Sandeep Belgavi."""
import unittest
from metrics import DOCS, QUERY, FOCUSED_CHUNKS, MIXED_CHUNKS, cosine, dot, mean, norm, rank, unit


class MetricTest(unittest.TestCase):
    def test_dot_prefers_the_long_vector(self):
        self.assertEqual(rank(QUERY, DOCS, 'dot'), ['gift-cards', 'returns-policy'])

    def test_cosine_and_l2_prefer_the_aligned_vector(self):
        self.assertEqual(rank(QUERY, DOCS, 'cosine'), ['returns-policy', 'gift-cards'])
        self.assertEqual(rank(QUERY, DOCS, 'l2'), ['returns-policy', 'gift-cards'])

    def test_quoted_numbers(self):
        self.assertAlmostEqual(dot(QUERY, DOCS['gift-cards']), 2.1)
        self.assertAlmostEqual(cosine(QUERY, DOCS['gift-cards']), 0.677, places=3)
        self.assertAlmostEqual(norm(DOCS['gift-cards']), 3.103, places=3)
        self.assertAlmostEqual(norm(DOCS['returns-policy']), 1.0)

    def test_after_normalising_all_three_metrics_agree(self):
        docs = {k: unit(v) for k, v in DOCS.items()}
        self.assertEqual(rank(QUERY, docs, 'dot'), rank(QUERY, docs, 'cosine'))
        self.assertEqual(rank(QUERY, docs, 'dot'), rank(QUERY, docs, 'l2'))

    def test_mean_pooling_shrinks_mixed_documents(self):
        self.assertAlmostEqual(norm(mean(FOCUSED_CHUNKS)), 0.998, places=3)
        self.assertAlmostEqual(norm(mean(MIXED_CHUNKS)), 0.577, places=3)
        # the on-topic chunk is identical to the query, yet dot drops the document to one third
        self.assertAlmostEqual(dot(QUERY, mean(MIXED_CHUNKS)), 1 / 3)
        self.assertAlmostEqual(cosine(QUERY, mean(MIXED_CHUNKS)), 0.577, places=3)


if __name__ == '__main__':
    unittest.main()
