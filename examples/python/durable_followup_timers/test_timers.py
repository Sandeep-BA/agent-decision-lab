# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import datetime as dt
import unittest
from timers import UTC, claim_due, connect, customer_replied, due_time, fire, run, schedule


class TimerTest(unittest.TestCase):
    def setUp(self):
        self.r = run()

    def test_friday_question_is_due_monday_0900_utc(self):
        self.assertEqual(due_time(dt.datetime(2026, 11, 20, 15, 30, tzinfo=UTC)).isoformat(), '2026-11-23T09:00:00+00:00')

    def test_sleep_in_loop_loses_every_wait_on_restart(self):
        self.assertEqual(self.r['sleep_in_loop_sent'], [])

    def test_reply_before_due_cancels_and_late_reply_loses(self):
        self.assertTrue(self.r['reply_cancelled_4102'])
        self.assertFalse(self.r['late_reply_cancelled_4103'])

    def test_two_workers_claim_each_timer_once(self):
        self.assertEqual(self.r['claims'], {'worker-a': ['CASE-4101', 'CASE-4103'], 'worker-b': []})

    def test_retried_fire_sends_one_message(self):
        self.assertEqual(self.r['outbox'], ['CASE-4101', 'CASE-4103'])
        self.assertEqual(self.r['states'], {'CASE-4101': 'fired', 'CASE-4102': 'cancelled', 'CASE-4103': 'fired'})

    def test_reasking_replaces_the_pending_timer(self):
        db = connect()
        schedule(db, 'CASE-4104', dt.datetime(2026, 11, 23, 10, 0, tzinfo=UTC))
        schedule(db, 'CASE-4104', dt.datetime(2026, 11, 24, 10, 0, tzinfo=UTC))
        rows = db.execute("SELECT due_at, state FROM timers WHERE case_id='CASE-4104'").fetchall()
        self.assertEqual(rows, [('2026-11-26T09:00:00+00:00', 'pending')])
        self.assertEqual(claim_due(db, 'w', dt.datetime(2026, 11, 25, 9, 0, tzinfo=UTC)), [])


if __name__ == '__main__':
    unittest.main()
