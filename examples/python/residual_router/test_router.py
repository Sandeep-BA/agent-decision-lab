"""Tests for the residual router example. Author: Sandeep Belgavi."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import router  # noqa: E402


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.invoices = router.fixture()

    def test_fixture_is_deterministic_and_complete(self):
        self.assertEqual(len(self.invoices), 1000)
        self.assertEqual(router.fixture(), self.invoices)

    def test_rules_decide_the_routine_cases_and_never_wrongly(self):
        r = router.run(0.8, invoices=self.invoices)
        self.assertEqual(r["rules"], 851)
        self.assertEqual(r["rules_wrong"], 0)
        self.assertEqual(r["agent_calls"], 149)

    def test_validator_refuses_unsafe_approvals_whatever_the_confidence(self):
        r = router.run(0.0, invoices=self.invoices)
        self.assertEqual(r["validator_refused"], 20)
        self.assertEqual(r["validator_reasons"], {"approval without a purchase order": 10,
                                                  "approval of goods not received": 6,
                                                  "approval above the agent limit": 4})

    def test_threshold_trades_automation_for_errors(self):
        loose, default, strict = (router.run(t, invoices=self.invoices) for t in (0.6, 0.8, 0.9))
        self.assertEqual((loose["agent_accepted"], loose["agent_wrong_accepted"]), (109, 4))
        self.assertEqual((default["agent_accepted"], default["agent_wrong_accepted"]), (105, 0))
        self.assertEqual(default["human_queue"], 44)
        self.assertEqual((strict["agent_accepted"], strict["human_queue"]), (9, 140))

    def test_escalations_always_reach_a_person(self):
        r = router.run(0.0, invoices=self.invoices)
        missing = [i for i in self.invoices if i.kind == "missing_po"]
        self.assertTrue(all(router.rules(i) is None for i in missing))
        self.assertGreaterEqual(r["human_queue"], 20)

    def test_promoted_rule_must_be_evaluated_like_any_change(self):
        r = router.run(0.8, freight_rule=True, invoices=self.invoices)
        self.assertEqual(r["rules"], 864)
        self.assertEqual(r["rules_wrong"], 4)   # it also approves small price errors

    def test_unknown_action_is_refused(self):
        self.assertEqual(router.validate(self.invoices[0], "pay_twice"), "unknown action")


if __name__ == "__main__":
    unittest.main()
