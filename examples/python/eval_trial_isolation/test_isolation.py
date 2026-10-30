"""Tests for isolation.py. Author: Sandeep Belgavi."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isolation as iso


class TrialIsolationTest(unittest.TestCase):
    def test_isolated_trials_measure_the_agent(self):
        results, unchanged = iso.suite('isolated')
        self.assertEqual([r['passed'] for r in results], [False, False, False])
        self.assertTrue(unchanged)

    def test_shared_state_inflates_later_trials(self):
        results, _ = iso.suite('shared')
        self.assertEqual([r['passed'] for r in results], [False, True, True])
        self.assertEqual(results[1]['result'], 'refunded')
        self.assertEqual(results[2]['result'], 'already refunded')

    def test_fingerprint_marks_leaked_trials_invalid(self):
        results, _ = iso.suite('shared', check=True)
        self.assertEqual(results[0]['passed'], False)
        self.assertIsNone(results[1]['passed'])
        self.assertTrue(results[2]['result'].startswith('invalid'))

    def test_each_trial_respects_the_budget(self):
        results, _ = iso.suite('isolated')
        self.assertTrue(all(r['calls'] <= iso.BUDGET for r in results))

    def test_template_is_never_written(self):
        for mode in ('shared', 'isolated'):
            self.assertTrue(iso.suite(mode)[1])


if __name__ == '__main__':
    unittest.main()
