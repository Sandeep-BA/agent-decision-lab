"""Author: Sandeep Belgavi. Tests for the guard mutation harness."""
import unittest
from example import GUARD_SOURCE, STRONG_SUITE, WEAK_SUITE, load, mutants, run_suite, score


class GuardMutation(unittest.TestCase):
    def test_both_suites_pass_on_the_real_guard(self):
        guard = load(GUARD_SOURCE)
        self.assertEqual(run_suite(guard, WEAK_SUITE), [])
        self.assertEqual(run_suite(guard, STRONG_SUITE), [])

    def test_mutants_are_distinct_programs(self):
        sources = [src for _, src in mutants()]
        self.assertEqual(len(sources), 26)
        self.assertEqual(len(set(sources)), len(sources))
        self.assertNotIn(GUARD_SOURCE.strip(), [s.strip() for s in sources])

    def test_weak_suite_leaves_boundary_mutants_alive(self):
        weak = score(WEAK_SUITE)
        self.assertEqual((weak["killed"], weak["survived"]), (13, 13))
        self.assertIn("line 9: constant 5000 -> 5001", weak["survivors"])
        self.assertIn("line 5: if-branch never taken", weak["survivors"])  # currency check unpinned

    def test_strong_suite_kills_every_mutant(self):
        self.assertEqual(score(STRONG_SUITE)["survived"], 0)

    def test_a_failing_suite_is_refused(self):
        with self.assertRaises(AssertionError):
            score([({"case_state": "verified", "currency": "INR", "order_currency": "INR",
                     "amount_cents": 10, "order_total_cents": 20, "prior_refunds": 0}, "reject")])


if __name__ == "__main__":
    unittest.main()
