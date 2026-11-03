"""Author: Sandeep Belgavi. Offline checks over the recorded runs; no model is called."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import selection as s  # noqa: E402


class SelectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs = s.load_recorded()

    def test_recorded_scores(self):
        got = {(m, v): s.score(r) for (m, v), r in self.runs.items()}
        self.assertEqual(got[("qwen2.5:1.5b", "v1")], 42)
        self.assertEqual(got[("qwen2.5:1.5b", "v2")], 42)
        self.assertEqual(got[("qwen2.5:1.5b", "v3")], 36)
        self.assertEqual(got[("qwen2.5:0.5b-instruct", "v1")], 34)
        self.assertEqual(got[("qwen2.5:0.5b-instruct", "v2")], 38)
        self.assertEqual(got[("qwen2.5:0.5b-instruct", "v3")], 29)

    def test_v2_changes_nothing_on_the_larger_model(self):
        self.assertEqual(s.diff(self.runs[("qwen2.5:1.5b", "v1")], self.runs[("qwen2.5:1.5b", "v2")]), {})

    def test_v3_moves_two_refund_cases_to_returns(self):
        moved = s.new_failures(self.runs[("qwen2.5:1.5b", "v1")], self.runs[("qwen2.5:1.5b", "v3")])
        self.assertEqual(moved, ["I already mailed back BK-1047 last week, where is my refund?",
                                 "You charged me twice for BK-1055, please refund one charge."])

    def test_a_higher_total_can_hide_a_new_failure(self):
        base, cand = self.runs[("qwen2.5:0.5b-instruct", "v1")], self.runs[("qwen2.5:0.5b-instruct", "v2")]
        self.assertGreater(s.score(cand), s.score(base))
        self.assertEqual(s.new_failures(base, cand), ["Is ISBN 9780140449136 available?"])

    def test_recorded_versions_match_the_code(self):
        self.assertEqual(len(s.CASES), 16)
        self.assertEqual(sorted({e for _, e in s.CASES}), ["check_stock", "issue_refund", "lookup_order", "start_return"])
        self.assertIn("getting money back", s.VERSIONS["v2"]["start_return"])


if __name__ == "__main__":
    unittest.main()
