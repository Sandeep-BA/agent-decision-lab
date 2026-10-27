"""Tests for the commit-token example. Author: Sandeep Belgavi."""
import unittest

from tokens import run_agent


class CommitTokenReads(unittest.TestCase):
    def test_lagging_replica_without_guards_refunds_twice(self):
        out = run_agent(lag=2.1)
        self.assertEqual(out["refunds_issued"], 2)
        self.assertTrue(out["agent_believed_first_failed"])

    def test_commit_token_falls_back_to_primary_when_replica_is_too_far_behind(self):
        out = run_agent(lag=2.1, use_tokens=True)
        self.assertEqual(out["refunds_issued"], 1)
        self.assertEqual(out["verification_read"]["served_by"], "primary")
        self.assertEqual(out["verification_read"]["refund"], "R1")

    def test_commit_token_waits_for_a_replica_that_catches_up_within_the_bound(self):
        out = run_agent(lag=0.6, use_tokens=True)
        self.assertEqual(out["verification_read"]["served_by"], "replica")
        self.assertEqual(out["verification_read"]["waited_s"], 0.25)
        self.assertEqual(out["refunds_issued"], 1)

    def test_freshness_flag_turns_none_into_unknown(self):
        out = run_agent(lag=2.1, report_freshness=True)
        self.assertEqual(out["verification_read"]["refund"], "unknown")
        self.assertFalse(out["verification_read"]["fresh"])
        self.assertEqual(out["refunds_issued"], 1)

    def test_intent_key_stops_the_duplicate_but_the_agent_still_misbelieves(self):
        out = run_agent(lag=2.1, intent_keys=True)
        self.assertEqual(out["refunds_issued"], 1)
        self.assertTrue(out["agent_believed_first_failed"])

    def test_no_lag_needs_no_guard(self):
        self.assertEqual(run_agent(lag=0.0)["refunds_issued"], 1)


if __name__ == "__main__":
    unittest.main()
