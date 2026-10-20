"""Tests for the agent tool contract example. Author: Sandeep Belgavi."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tool_contracts as t  # noqa: E402


class ContractVerification(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(t.CONTRACT.read_text(encoding="utf-8"))

    def test_reference_provider_satisfies_every_recorded_interaction(self):
        self.assertEqual(t.verify(self.contract, "v1"), {})

    def test_renaming_a_field_an_agent_reads_fails_exactly_those_interactions(self):
        failures = t.verify(self.contract, "renamed")
        self.assertEqual(sorted(failures), ["i1-full-flow", "i3-second-order"])
        self.assertIn("result no longer carries remaining_refundable", failures["i1-full-flow"])

    def test_accepting_a_call_that_used_to_be_rejected_fails(self):
        failures = t.verify(self.contract, "lenient")
        self.assertEqual(list(failures), ["i4-negative-amount-rejected"])
        self.assertIn("call that used to be rejected is now accepted", failures["i4-negative-amount-rejected"])

    def test_missing_required_argument_is_reported(self):
        call = {"arguments": {"order_id": "o-1", "amount": 5, "reason": "x"}, "fields_read_next": []}
        provider = lambda args: {"error": "bad request"}
        self.assertEqual(t.check_interaction(self.contract["tool"]["inputSchema"], call, provider),
                         ["missing required argument idempotency_key"])


class Replay(unittest.TestCase):
    def setUp(self):
        self.store = json.loads(t.REPLAYS.read_text(encoding="utf-8"))

    def test_recorded_turn_replays_deterministically(self):
        out = t.run_turn(t.ReplayModel(self.store), t.RefundService(), "My order o-1 arrived a week late, can I get 40 back?")
        self.assertEqual(out["tool_result"], {"refund_id": "rf-1", "amount": 40, "remaining_refundable": 60})
        self.assertIn("60", out["answer"])

    def test_unrecorded_request_fails_instead_of_calling_a_live_model(self):
        with self.assertRaises(t.ReplayMiss):
            t.run_turn(t.ReplayModel(self.store), t.RefundService(), "A prompt that was never recorded")

    def test_fixture_matches_the_recording_job(self):
        self.assertEqual(self.store, t.record_fixture())


class Invariants(unittest.TestCase):
    def test_buggy_handler_over_refunds_and_shrinks_to_two_calls(self):
        out = t.check_invariants(check_cap=False, seed=7)
        self.assertIsNotNone(out["failed_after"])
        minimal = out["minimal"]
        self.assertEqual(len(minimal), 2)
        self.assertEqual(minimal[0]["order_id"], minimal[1]["order_id"])
        self.assertNotEqual(minimal[0]["idempotency_key"], minimal[1]["idempotency_key"])

    def test_fixed_handler_holds_for_many_seeds(self):
        for seed in range(20):
            self.assertIsNone(t.check_invariants(check_cap=True, seed=seed)["failed_after"], seed)

    def test_retry_with_same_key_never_creates_a_second_effect(self):
        s = t.RefundService()
        first = s.refund_order("o-1", 40, "late", "o-1:conv-7")
        again = s.refund_order("o-1", 40, "late, second wording", "o-1:conv-7")
        self.assertEqual(first, again)
        self.assertEqual(s.refunded("o-1"), 40)


if __name__ == "__main__":
    unittest.main()
