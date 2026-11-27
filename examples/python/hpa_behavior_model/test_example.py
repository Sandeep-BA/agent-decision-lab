"""Tests for hpa_behavior_model. Author: Sandeep Belgavi."""
import io, json, unittest
from contextlib import redirect_stdout
from pathlib import Path
import example as ex


class HpaBehaviorModel(unittest.TestCase):
    def test_report_matches_recorded_expected_output(self):
        with redirect_stdout(io.StringIO()):
            report = ex.main()
        self.assertEqual(report, json.loads((Path(__file__).parent / 'expected.json').read_text(encoding='utf-8')))

    def test_tolerance_suppresses_small_ratios(self):
        self.assertEqual(ex.raw_desired(20, 1280, 60, 0.1, 0.1), (20, 1280 / 20 / 60))
        self.assertEqual(ex.raw_desired(20, 1400, 60, 0.1, 0.1)[0], 24)

    def test_percent_down_policy_truncates_like_the_controller(self):
        rules = {'selectPolicy': 'Max', 'policies': [{'type': 'Percent', 'value': 10, 'periodSeconds': 60}]}
        self.assertEqual(ex.down_limit(72, [], [], rules, 0), 64)

    def test_max_select_takes_the_largest_allowed_change(self):
        rules = {'selectPolicy': 'Max', 'policies': [{'type': 'Pods', 'value': 4, 'periodSeconds': 60}, {'type': 'Percent', 'value': 10, 'periodSeconds': 60}]}
        self.assertEqual(ex.down_limit(80, [], [], rules, 0), 72)
        self.assertEqual(ex.down_limit(30, [], [], rules, 0), 26)
        self.assertEqual(ex.down_limit(30, [], [], dict(rules, selectPolicy='Min'), 0), 27)

    def test_changes_inside_the_period_count_against_the_policy(self):
        rules = {'selectPolicy': 'Max', 'policies': [{'type': 'Pods', 'value': 2, 'periodSeconds': 60}]}
        self.assertEqual(ex.down_limit(18, [], [(0, 2)], rules, 30), 18)
        self.assertEqual(ex.down_limit(18, [], [(0, 2)], rules, 60), 16)

    def test_default_window_holds_replicas_for_about_five_minutes(self):
        rows = ex.simulate(ex.drop, 600, 20, 60, 2, 30)
        self.assertTrue(all(r['replicas_after'] == 20 for r in rows if r['t'] < 285))
        self.assertEqual(ex.first_time_at(rows, 5), 285)

    def test_scale_up_is_limited_by_the_default_policies(self):
        rows = ex.simulate(lambda now: 600 if now < 0 else 2400, 30, 10, 60, 2, 50, warmup=60)
        self.assertEqual(rows[0]['replicas_after'], 20)

    def test_disabled_scale_down_never_removes_pods(self):
        rows = ex.simulate(ex.drop, 600, 20, 60, 2, 30, down={'selectPolicy': 'Disabled'})
        self.assertTrue(all(r['replicas_after'] == 20 for r in rows))


if __name__ == '__main__':
    unittest.main()
