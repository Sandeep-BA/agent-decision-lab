"""Author: Sandeep Belgavi. Expected outcomes for the visibility-timeout model."""
import unittest
from visibility import simulate


class VisibilityTests(unittest.TestCase):
    def test_default_redelivers_until_dead_letter(self):
        r = simulate()
        self.assertEqual(r.outcome, "dead-letter")
        self.assertEqual([t for t, _, _ in r.receives], [0, 30, 60, 90, 120])
        self.assertEqual(r.replies, 5)
        self.assertEqual(r.model_seconds, 225)

    def test_heartbeat_shorter_than_timeout_keeps_ownership(self):
        r = simulate(heartbeat=10)
        self.assertEqual((r.outcome, len(r.receives), r.replies), ("deleted", 1, 1))

    def test_heartbeat_equal_to_timeout_is_too_late(self):
        r = simulate(heartbeat=30)
        self.assertEqual((r.outcome, len(r.receives), r.replies), ("dead-letter", 5, 5))

    def test_heartbeat_twenty_seconds(self):
        r = simulate(heartbeat=20)
        self.assertEqual((r.outcome, r.replies), ("deleted", 1))

    def test_longer_timeout(self):
        r = simulate(visibility=60)
        self.assertEqual((r.outcome, len(r.receives)), ("deleted", 1))

    def test_idempotency_key_stops_duplicate_replies_not_redelivery(self):
        r = simulate(idempotency_key=True)
        self.assertEqual((r.outcome, r.replies, r.suppressed, r.model_seconds), ("dead-letter", 1, 4, 225))

    def test_max_receive_count_two(self):
        r = simulate(max_receives=2)
        self.assertEqual((r.outcome, len(r.receives), r.replies), ("dead-letter", 2, 2))

    def test_step_just_under_timeout(self):
        self.assertEqual(simulate(step=29).outcome, "deleted")
        self.assertEqual(simulate(step=30, max_receives=3).outcome, "dead-letter")

    def test_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            simulate(visibility=0)


if __name__ == "__main__":
    unittest.main()
