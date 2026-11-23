"""Author: Sandeep Belgavi. Expected outcomes for the quorum join example."""
import unittest
import join as J


class QuorumJoinTest(unittest.TestCase):
    def test_all_waits_for_the_slowest_and_escalates_on_a_failure(self):
        r = J.join(J.SUBTASKS, 'all', 12.0)
        self.assertEqual((r['decided_at'], r['verdict']), (9.0, 'escalate'))
        self.assertEqual(r['failed'], ['payment-check'])

    def test_all_with_a_deadline_escalates_at_the_deadline(self):
        r = J.join(J.SUBTASKS, 'all', 5.0)
        self.assertEqual((r['decided_at'], r['verdict']), (5.0, 'escalate'))
        self.assertEqual(r['cancel_or_ignore_late'], ['fraud-signals'])

    def test_two_of_n_decides_when_two_agree_and_names_them(self):
        r = J.join(J.SUBTASKS, 'quorum', 5.0, 2)
        self.assertEqual((r['decided_at'], r['verdict'], r['used']), (2.5, 'approve', ['policy-reader', 'order-history']))
        self.assertEqual(r['cancel_or_ignore_late'], ['fraud-signals'])

    def test_a_failure_does_not_count_towards_the_quorum(self):
        r = J.join(J.SUBTASKS, 'quorum', 5.0, 3)
        self.assertEqual(r['verdict'], 'escalate')
        self.assertIn('deadline', r['reason'])

    def test_late_dissent_never_changes_a_decision(self):
        r = J.join(J.SUBTASKS, 'quorum', 12.0, 2)
        self.assertEqual((r['decided_at'], r['verdict']), (2.5, 'approve'))
        self.assertNotIn('fraud-signals', r['used'])

    def test_first_valid_skips_failures(self):
        r = J.join([J.Subtask('a', 0.5, None, 'boom'), J.Subtask('b', 1.0, 'reject')], 'first_valid', 5.0)
        self.assertEqual((r['decided_at'], r['verdict'], r['used'], r['failed']), (1.0, 'reject', ['b'], ['a']))

    def test_a_required_veto_check_is_waited_for_and_can_reject(self):
        r = J.join(J.SUBTASKS, 'quorum', 12.0, 2, required=('fraud-signals',))
        self.assertEqual((r['decided_at'], r['verdict'], r['used']), (9.0, 'reject', ['fraud-signals']))
        r = J.join(J.SUBTASKS, 'quorum', 5.0, 2, required=('fraud-signals',))
        self.assertEqual((r['decided_at'], r['verdict']), (5.0, 'escalate'))

    def test_inputs_are_validated(self):
        with self.assertRaises(ValueError):
            J.join(J.SUBTASKS, 'majority', 5.0)
        with self.assertRaises(ValueError):
            J.join(J.SUBTASKS, 'quorum', 0, 2)


if __name__ == '__main__':
    unittest.main()
