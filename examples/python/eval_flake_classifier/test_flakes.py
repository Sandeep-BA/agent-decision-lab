"""Tests for the flaky-eval classifier; numbers match the article's tables. Author: Sandeep Belgavi."""
import datetime as dt
import unittest

import flakes as f


class PlantedFaults(unittest.TestCase):
    def test_real_clock_breaks_case_6001_and_frozen_clock_fixes_it(self):
        self.assertFalse(f.case_6001(lambda: dt.date(2026, 11, 6)))
        self.assertTrue(f.case_6001(lambda: f.FIXTURE_ORDER_DATE + dt.timedelta(days=10)))
        self.assertFalse(f.case_6001(lambda: f.FIXTURE_ORDER_DATE + dt.timedelta(days=40)))

    def test_set_based_tool_needs_set_comparison(self):
        out = f.recommend(['Atlas', 'Cookbook', 'Lamp'])
        self.assertEqual(set(out), {'Atlas', 'Cookbook', 'Lamp'})

    def test_shared_sandbox_fails_only_with_a_parallel_neighbour(self):
        self.assertTrue(f.case_cancel_status(f.SharedSandbox(), parallel_neighbour_runs=False))
        self.assertFalse(f.case_cancel_status(f.SharedSandbox(), parallel_neighbour_runs=True))


class Classify(unittest.TestCase):
    def run_(self, mode, passed, parallel=False, error=None):
        return {'mode': mode, 'parallel': parallel, 'passed': passed, 'error': error}

    def test_article_example_is_shared_state(self):
        runs = [self.run_('replay', i % 3 != 0, True) for i in range(6)] + [self.run_('replay', True) for _ in range(4)]
        self.assertEqual(f.classify(runs), 'shared state')

    def test_replay_variation_without_parallelism_is_harness(self):
        self.assertEqual(f.classify([self.run_('replay', True), self.run_('replay', False)]), 'harness')

    def test_stable_replay_varying_live_is_model_variance(self):
        runs = [self.run_('replay', True)] * 3 + f.simulate_live(0.8, 20, seed=7)
        self.assertEqual(f.classify(runs), 'model variance')

    def test_errors_are_infrastructure(self):
        self.assertEqual(f.classify([self.run_('live', False, error='timeout')]), 'infrastructure: timeout')


class Arithmetic(unittest.TestCase):
    def test_runs_needed_table(self):
        self.assertEqual([f.runs_needed(p) for p in (0.2, 0.1, 0.05, 0.02)], [14, 29, 59, 149])

    def test_chance_ten_clean_runs_miss_a_5_percent_flake(self):
        self.assertAlmostEqual(0.95 ** 10, 0.599, places=3)

    def test_pass_hat_k(self):
        self.assertEqual(f.pass_hat_k(16, 16, 4), 1.0)
        self.assertAlmostEqual(f.pass_hat_k(12, 16, 4), 495 / 1820)


if __name__ == '__main__':
    unittest.main()
