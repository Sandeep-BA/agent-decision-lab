"""Author: Sandeep Belgavi. Tests for post-filtered nearest-neighbour survivor counts."""
import json
import unittest
from pathlib import Path
from example import CANDIDATES, K, build, dist, main, ranked, strategies


class FilteredSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = main()

    def test_ten_percent_filter_leaves_about_four(self):
        r = self.res["promo (10%, independent of topic)"]
        self.assertEqual(r["post_filter_returned"], 4)
        self.assertEqual(r["iterative_visited"], 120)

    def test_one_percent_filter_needs_large_overfetch(self):
        r = self.res["rare (1%, independent of topic)"]
        self.assertEqual([r["post_filter_returned"], r["overfetch_x4_returned"], r["overfetch_x10_returned"], r["overfetch_x40_returned"]], [1, 4, 7, 10])

    def test_clustered_filter_starves_overfetch(self):
        far = [v for k, v in self.res.items() if "farthest" in k][0]
        self.assertEqual(far["overfetch_x40_returned"], 0)
        self.assertEqual(far["iterative_returned"], K)
        self.assertGreater(far["iterative_visited"], 15_000)

    def test_prefilter_is_always_complete(self):
        self.assertTrue(all(r["prefilter_returned"] == K for r in self.res.values()))

    def test_iterative_never_returns_wrong_order_items(self):
        centers, items = build()
        order = ranked(items, [c + 0.1 for c in centers[0]])
        self.assertLessEqual(dist(order[0]["vec"], centers[0]), dist(order[-1]["vec"], centers[0]))
        out = strategies(order, lambda it: True)
        self.assertEqual(out["post_filter_returned"], K)
        self.assertEqual(out["iterative_visited"], CANDIDATES)

    def test_expected_file_matches(self):
        expected = json.loads(Path(__file__).with_name("expected.json").read_text(encoding="utf-8"))
        self.assertEqual(self.res, expected)


if __name__ == "__main__":
    unittest.main()
