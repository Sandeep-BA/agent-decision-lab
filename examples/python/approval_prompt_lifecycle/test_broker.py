"""Author: Sandeep Belgavi. Expected outcomes for the approval broker."""
import unittest
from broker import Broker, Request, demo


class BrokerTests(unittest.TestCase):
    def test_one_prompt_per_endpoint(self):
        b = demo()
        self.assertEqual([rid for _, rid in b.shown], ["r1", "r4"])

    def test_one_time_decision_lets_the_next_request_prompt(self):
        b = demo()
        b.decide("p1", "allow-once", "t1")
        self.assertEqual(b.shown[-1], ("p3", "r2"))

    def test_session_grant_resolves_waiting_requests(self):
        b = demo()
        b.decide("p1", "allow-session", "t1")
        self.assertEqual((b.results["r2"], b.results["r3"]), ("allowed", "allowed"))
        self.assertEqual(len(b.shown), 2)

    def test_withdrawal_then_late_decision_is_rejected(self):
        b = demo()
        b.request_ended("r1")
        self.assertEqual(b.results["r1"], "withdrawn")
        self.assertFalse(b.decide("p1", "allow-session", "t1"))
        self.assertNotIn(("local", "registry.npmjs.org", "https", 443), b.session_grants)
        self.assertEqual(b.shown[-1][1], "r2")

    def test_decision_from_another_turn_is_rejected(self):
        b = demo()
        self.assertFalse(b.decide("p1", "allow-once", "t2"))
        self.assertNotIn("r1", b.results)

    def test_unattended_denies_and_continues(self):
        b = demo(unattended=True)
        self.assertEqual(set(b.results.values()), {"denied"})
        self.assertEqual(b.shown, [])

    def test_existing_grant_applies_even_unattended(self):
        b = Broker(unattended=True)
        b.session_grants.add(("local", "registry.npmjs.org", "https", 443))
        b.submit(Request("r9", "t5", "registry.npmjs.org"))
        self.assertEqual(b.results["r9"], "allowed")


if __name__ == "__main__":
    unittest.main()
