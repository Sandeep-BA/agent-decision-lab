# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import asyncio
import unittest
from outcomes import derive_outcome, naive_taskgroup, separated

ALL_OK = {'order_lookup': 'ok', 'refund_amount': 'ok', 'tone_review': 'ok', 'reading_suggestion': 'ok'}


class OutcomeTest(unittest.TestCase):
    def test_naive_group_cancels_required_work(self):
        states = asyncio.run(naive_taskgroup(fail={'tone_review'}))
        self.assertEqual(states['order_lookup'], 'cancelled')
        self.assertEqual(states['refund_amount'], 'cancelled')
        self.assertEqual(derive_outcome(states)['outcome'], 'failed')

    def test_separated_optional_failure_is_a_warning(self):
        states = asyncio.run(separated(fail={'tone_review'}))
        r = derive_outcome(states)
        self.assertEqual(r['outcome'], 'succeeded_with_warnings')
        self.assertEqual(r['warnings'], ['tone_review failed'])

    def test_slow_optional_check_times_out_without_failing(self):
        states = asyncio.run(separated(slow={'reading_suggestion'}))
        self.assertEqual(states['reading_suggestion'], 'timed_out')
        self.assertEqual(derive_outcome(states)['outcome'], 'succeeded_with_warnings')

    def test_required_failure_fails(self):
        states = asyncio.run(separated(fail={'refund_amount'}))
        r = derive_outcome(states)
        self.assertEqual(r['outcome'], 'failed')
        self.assertIn('refund_amount failed', r['problems'])

    def test_pending_required_is_running_not_success(self):
        self.assertEqual(derive_outcome({**ALL_OK, 'refund_amount': 'pending'})['outcome'], 'running')

    def test_pending_optional_at_decision_point_fails(self):
        self.assertEqual(derive_outcome({**ALL_OK, 'tone_review': 'pending'})['outcome'], 'failed')

    def test_skips_need_a_reason(self):
        self.assertEqual(derive_outcome({**ALL_OK, 'tone_review': 'skipped'})['outcome'], 'failed')
        self.assertEqual(derive_outcome({**ALL_OK, 'tone_review': 'skipped'}, {'tone_review': 'APPROVAL-17'})['outcome'], 'succeeded_with_warnings')
        self.assertEqual(derive_outcome({**ALL_OK, 'order_lookup': 'skipped'})['outcome'], 'failed')

    def test_missing_or_unknown_task_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no state'):
            derive_outcome({'order_lookup': 'ok'})
        with self.assertRaisesRegex(ValueError, 'unknown'):
            derive_outcome({**ALL_OK, 'surprise': 'ok'})


if __name__ == '__main__':
    unittest.main()
