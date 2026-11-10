"""Author: Sandeep Belgavi."""
import datetime
import unittest
from nightly import Crash, State, check_draft, fixture, key_for, run, select_due

RUN = datetime.date(2026, 11, 10)


def polite(order):
    return f"Hello {order['reader']}, {order['title']} on {order['order_id']} is overdue. Please return it when you can."


class NightlyJob(unittest.TestCase):
    def test_selection_ignores_the_drafter(self):
        self.assertEqual([o['order_id'] for o in select_due(fixture(), RUN)], ['ORD-201', 'ORD-204', 'ORD-205'])

    def test_crash_after_send_then_rerun_sends_each_once(self):
        state = State()
        with self.assertRaises(Crash):
            run(fixture(), RUN, polite, state, crash_after_send='ORD-204')
        self.assertEqual(state.checkpoint, 'ORD-201')     # ORD-204 was sent, checkpoint not advanced
        run(fixture(), RUN, polite, state)
        self.assertEqual([oid for _, oid, _ in state.outbox], ['ORD-201', 'ORD-204', 'ORD-205'])
        self.assertEqual(len(state.ledger), 3)

    def test_fresh_checkpoint_same_day_still_does_not_resend(self):
        state = run(fixture(), RUN, polite, State())
        state.checkpoint = ''                             # lost checkpoint file
        run(fixture(), RUN, polite, state)
        self.assertEqual(len(state.outbox), 3)

    def test_bad_or_failing_drafts_leave_the_send_path(self):
        def drafter(order):
            if order['order_id'] == 'ORD-201':
                return 'We will waive the fee and refund you. ORD-201'
            if order['order_id'] == 'ORD-204':
                raise TimeoutError('provider timeout')
            return polite(order)
        state = run(fixture(), RUN, drafter, State())
        self.assertEqual([oid for _, oid, _ in state.outbox], ['ORD-205'])
        self.assertEqual(state.review[0][0], 'ORD-201')
        self.assertEqual(state.retry, [('ORD-204', 'TimeoutError')])

    def test_check_draft_rules(self):
        order = fixture()[0]
        self.assertIsNone(check_draft(order, polite(order)))
        self.assertEqual(check_draft(order, 'Please return the book.'), 'draft does not cite the order id')
        self.assertEqual(check_draft(order, 'x' * 601), 'draft longer than 600 characters')
        self.assertEqual(key_for(RUN, 'ORD-201'), '2026-11-10:ORD-201:overdue-reminder-v1')


if __name__ == '__main__':
    unittest.main()
