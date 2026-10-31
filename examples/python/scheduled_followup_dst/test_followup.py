"""Author: Sandeep Belgavi. Tests for scheduled_followup_dst against the 2026 transitions."""
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from followup import FollowUp, Runner, classify, due_instant, naive_instant, utc


class TransitionTests(unittest.TestCase):
    def test_london_after_october_25_is_utc_plus_zero(self):
        f = FollowUp('CASE-5104', datetime(2026, 11, 1, 14, 30), 'Europe/London')
        self.assertEqual(due_instant(f), utc(2026, 11, 1, 14, 30))
        self.assertEqual(naive_instant(f, utc(2026, 10, 21, 14, 32)), utc(2026, 11, 1, 13, 30))

    def test_new_york_repeated_hour_has_two_instants(self):
        f = FollowUp('CASE-5121', datetime(2026, 11, 1, 1, 30), 'America/New_York')
        self.assertEqual(classify(f), 'repeated')
        self.assertEqual(due_instant(f), utc(2026, 11, 1, 5, 30))
        later = FollowUp(f.case_id, f.local_time, f.zone, repeated='later')
        self.assertEqual(due_instant(later), utc(2026, 11, 1, 6, 30))

    def test_new_york_missing_hour_moves_forward_or_skips(self):
        f = FollowUp('CASE-5122', datetime(2027, 3, 14, 2, 30), 'America/New_York')
        self.assertEqual(classify(f), 'missing')
        local = due_instant(f).astimezone(ZoneInfo('America/New_York'))
        self.assertEqual((local.hour, local.minute), (3, 30))
        self.assertIsNone(due_instant(FollowUp(f.case_id, f.local_time, f.zone, missing='skip')))

    def test_kolkata_has_no_transition(self):
        f = FollowUp('CASE-5130', datetime(2026, 11, 1, 1, 30), 'Asia/Kolkata')
        self.assertEqual(classify(f), 'ordinary')
        self.assertEqual(due_instant(f), utc(2026, 10, 31, 20, 0))

    def test_offsets_are_rejected(self):
        with self.assertRaises(ValueError):
            FollowUp('CASE-1', datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc), 'Europe/London')


class RunnerTests(unittest.TestCase):
    def test_sends_once_and_rechecks_the_case(self):
        open_cases, sent = {'CASE-5104'}, []
        runner = Runner(lambda c: c in open_cases, sent.append)
        f = FollowUp('CASE-5104', datetime(2026, 11, 1, 14, 30), 'Europe/London')
        self.assertEqual(runner.run_once(f, utc(2026, 11, 1, 14, 0)), 'not due')
        self.assertEqual(runner.run_once(f, utc(2026, 11, 1, 14, 30)), 'sent')
        self.assertEqual(runner.run_once(f, utc(2026, 11, 1, 14, 31)), 'duplicate suppressed')
        open_cases.clear()
        g = FollowUp('CASE-5104', datetime(2026, 11, 2, 9, 0), 'Europe/London')
        self.assertEqual(runner.run_once(g, utc(2026, 11, 2, 9, 0)), 'skipped: precondition no longer holds')
        self.assertEqual(len(sent), 1)


if __name__ == '__main__':
    unittest.main()
