"""Tests for mcp_timeout_clock. Author: Sandeep Belgavi."""
import io, json, unittest
from contextlib import redirect_stdout
from pathlib import Path
import example as ex


class McpTimeoutClock(unittest.TestCase):
    def test_report_matches_recorded_expected_output(self):
        with redirect_stdout(io.StringIO()):
            report = ex.main()
        self.assertEqual(report, json.loads((Path(__file__).parent / 'expected.json').read_text(encoding='utf-8')))

    def test_progress_without_reset_does_not_extend_the_deadline(self):
        r = ex.simulate(60000, False, 0, 'sdk', [20000, 40000], 90000)
        self.assertEqual((r['outcome'], r['stopped_waiting_ms'], r['late_result_ignored']), ('idle-timeout', 60000, True))

    def test_reset_moves_the_deadline_from_each_notification(self):
        r = ex.simulate(60000, True, 0, 'sdk', [50000, 100000], 155000)
        self.assertEqual(r['outcome'], 'result')
        self.assertEqual(r['progress_resets'], 2)

    def test_sdk_ceiling_is_only_checked_when_progress_arrives(self):
        r = ex.simulate(60000, True, 300000, 'sdk', [50000, 100000, 150000, 200000, 250000, 290000], None)
        self.assertEqual((r['outcome'], r['stopped_waiting_ms']), ('idle-timeout', 350000))

    def test_timer_ceiling_fires_at_the_ceiling_and_cancels(self):
        r = ex.simulate(60000, True, 300000, 'timer', [50000, 100000, 150000, 200000, 250000, 290000], None)
        self.assertEqual((r['outcome'], r['stopped_waiting_ms'], r['cancellation_sent']), ('ceiling-cancelled', 300000, True))

    def test_sdk_max_total_rejection_sends_no_cancellation(self):
        r = ex.simulate(60000, True, 300000, 'sdk', list(range(25000, 600001, 25000)), None)
        self.assertEqual((r['outcome'], r['cancellation_sent']), ('max-total-exceeded', False))

    def test_result_after_deadline_is_late(self):
        r = ex.simulate(1000, True, 0, 'sdk', [], 1500)
        self.assertTrue(r['late_result_ignored'])
        self.assertIn('late result', r['trace'][-1])

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            ex.simulate(0, True, 0, 'sdk', [], None)
        with self.assertRaises(ValueError):
            ex.simulate(1000, True, 0, 'other', [], None)

    def test_worst_case_bounds(self):
        self.assertEqual(ex.worst_case_wait(60000, 300000, 'sdk'), 360000)
        self.assertEqual(ex.worst_case_wait(60000, 300000, 'timer'), 300000)
        self.assertIsNone(ex.worst_case_wait(60000, 0, 'sdk'))


if __name__ == '__main__':
    unittest.main()
