"""Tests for the agent cost forecast example. Author: Sandeep Belgavi."""
import unittest

from forecast import (equivalents, forecast, reweighted, run_tokens, synthetic_runs, tail_share)


class RunTokens(unittest.TestCase):
    def test_eight_step_run_matches_the_worked_example(self):
        u = run_tokens(8)
        self.assertEqual((u["input"], u["output"], u["cache_read"], u["cache_write"]), (96400, 2400, 85100, 11300))
        self.assertEqual(u["cache_read"] + u["cache_write"], u["input"])

    def test_doubling_steps_triples_input(self):
        self.assertEqual(run_tokens(16)["input"], 288800)
        self.assertAlmostEqual(run_tokens(16)["input"] / run_tokens(8)["input"], 2.996, places=3)

    def test_cache_cuts_an_eight_step_run_to_a_third(self):
        self.assertEqual(round(equivalents(run_tokens(8))), 34635)
        self.assertEqual(round(equivalents(run_tokens(8), cached=False)), 108400)


class Forecast(unittest.TestCase):
    def setUp(self):
        self.pilot = synthetic_runs(60, seed=2026)
        self.week = synthetic_runs(1400, seed=99, long_share=0.15)

    def test_pilot_has_few_long_runs_and_a_heavy_tail(self):
        self.assertEqual(sum(s >= 18 for s in self.pilot), 2)
        self.assertEqual(tail_share(self.pilot), 0.215)

    def test_bootstrap_interval_misses_a_mix_shift(self):
        f = forecast(self.pilot, 1400)
        self.assertEqual((f["p10"], f["p50"], f["p90"]), (45142195, 46008660, 46876350))
        actual = round(sum(equivalents(run_tokens(s)) for s in self.week))
        self.assertEqual(actual, 65996465)
        self.assertGreater(actual, f["p90"])

    def test_reweighting_by_observed_long_share_explains_most_of_the_gap(self):
        share = sum(s >= 18 for s in self.week) / len(self.week)
        self.assertEqual(sum(s >= 18 for s in self.week), 234)
        self.assertEqual(reweighted(self.pilot, 1400, share), 62165977)

    def test_forecast_is_deterministic(self):
        self.assertEqual(forecast(self.pilot, 100), forecast(self.pilot, 100))


if __name__ == "__main__":
    unittest.main()
