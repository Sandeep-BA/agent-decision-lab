"""Tests for the online evaluation example. Author: Sandeep Belgavi."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import online_eval as e  # noqa: E402

REF = e.SCENARIOS["reference"]
WEEKS = e.SCENARIOS["weeks"]


def report(week, how, seed, budget=600):
    runs = e.make_runs(WEEKS[week], 20000, seed)
    return e.weekly_report(runs, budget, how, REF, seed + 1)


class Statistics(unittest.TestCase):
    def test_wilson_matches_the_guide(self):
        self.assertEqual(tuple(round(x, 3) for x in e.wilson(33, 60)), (0.425, 0.669))
        self.assertEqual(tuple(round(x, 3) for x in e.wilson(110, 200)), (0.481, 0.617))
        self.assertEqual(tuple(round(x, 3) for x in e.wilson(13, 24)), (0.351, 0.721))
        self.assertEqual(e.wilson(0, 0), (0.0, 1.0))

    def test_decomposition_matches_the_guide(self):
        self.assertEqual(e.decompose(REF, WEEKS["hidden-regression"]), (2.9, -1.5))
        self.assertEqual(e.decompose(REF, WEEKS["mix-shift"]), (-4.4, 0.0))
        self.assertEqual(e.decompose(REF, WEEKS["unchanged"]), (0.0, 0.0))

    def test_allocations_spend_the_budget(self):
        counts = {"billing": 14000, "account": 4000, "technical": 2000}
        self.assertEqual(e.allocate(counts, 600, "uniform", REF["rates"]), {"billing": 420, "account": 120, "technical": 60})
        self.assertEqual(e.allocate(counts, 600, "equal", REF["rates"]), {"billing": 200, "account": 200, "technical": 200})
        ney = e.allocate(counts, 600, "neyman", REF["rates"])
        self.assertAlmostEqual(sum(ney.values()), 600, delta=1)
        self.assertGreater(ney["technical"] / 2000, ney["billing"] / 14000)   # higher variance, sampled more densely


class Scenarios(unittest.TestCase):
    def test_hidden_regression_aggregate_rises_but_reweighted_falls(self):
        for seed in range(10):
            rep = report("hidden-regression", "equal", seed)
            self.assertGreater(rep["reweighted"], 0.75, seed)
            self.assertLess(rep["reweighted"], rep["baseline_aggregate"], seed)

    def test_equal_allocation_catches_the_technical_regression(self):
        hits = sum(report("hidden-regression", "equal", seed)["rows"][2]["alert"] for seed in range(20))
        self.assertGreaterEqual(hits, 19)

    def test_equal_allocation_is_at_least_as_sensitive_as_uniform(self):
        equal = sum(report("hidden-regression", "equal", s)["rows"][2]["alert"] for s in range(30))
        uniform = sum(report("hidden-regression", "uniform", s)["rows"][2]["alert"] for s in range(30))
        self.assertGreaterEqual(equal, uniform)

    def test_mix_shift_moves_the_aggregate_not_the_segments(self):
        alarms = segment_alerts = 0
        for seed in range(20):
            rep = report("mix-shift", "equal", seed)
            alarms += e.aggregate_alert(rep)
            segment_alerts += sum(r["alert"] for r in rep["rows"])
            self.assertAlmostEqual(rep["reweighted"], rep["baseline_aggregate"], delta=0.05)
        self.assertGreaterEqual(alarms, 15)          # the aggregate rule fires on mix alone
        self.assertLessEqual(segment_alerts, 3)       # segment rules mostly stay quiet


if __name__ == "__main__":
    unittest.main()
