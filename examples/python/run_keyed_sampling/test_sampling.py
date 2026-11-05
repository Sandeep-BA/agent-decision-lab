"""Tests for run_keyed_sampling. Author: Sandeep Belgavi. Run: python -m unittest -v"""
import re, unittest
from sampling import keep, rv_for_run, sample, synthetic_runs, threshold, tracestate_for_run


class ThresholdTest(unittest.TestCase):
    def test_spec_example_one_percent(self):
        # OpenTelemetry: 1% has rejection threshold 0xfd70a3d70a3d71 (encoded th:fd70a4 at 5 digits)
        self.assertEqual('%014x' % threshold(0.01), 'fd70a3d70a3d71')

    def test_keep_all_and_bounds(self):
        self.assertEqual(threshold(1), 0)
        self.assertTrue(keep(0, 1.0))
        with self.assertRaises(ValueError):
            threshold(0)

    def test_higher_probability_keeps_a_superset(self):
        for r in (0, 1 << 50, (1 << 56) - 1, int(rv_for_run('run-7'), 16)):
            if keep(r, 0.1):
                self.assertTrue(keep(r, 0.25))


class RunKeyTest(unittest.TestCase):
    def test_rv_is_fourteen_lower_hex_digits(self):
        self.assertRegex(rv_for_run('run-00042'), r'^[0-9a-f]{14}$')
        self.assertEqual(tracestate_for_run('run-00042'), 'ot=rv:8a84c66f6e2dda')

    def test_run_policy_never_splits_a_run(self):
        runs = synthetic_runs(2000)
        for p in (0.1, 0.25, 0.5):
            self.assertEqual(sample(runs, p, 'run')['partial'], 0)

    def test_numbers_quoted_in_the_readme(self):
        runs = synthetic_runs(2000)
        t, r = sample(runs, 0.1, 'trace'), sample(runs, 0.1, 'run')
        self.assertEqual((t['kept_whole'], t['partial'], t['traces_kept']), (51, 389, 485))
        self.assertEqual((r['kept_whole'], r['partial'], r['traces_kept']), (203, 0, 530))
        self.assertEqual((r['traces'], sum(1 for _, n in runs if n > 1)), (5081, 1500))


if __name__ == '__main__':
    unittest.main()
