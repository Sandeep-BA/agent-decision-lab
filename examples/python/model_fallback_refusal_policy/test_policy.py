"""Tests for the refusal fallback policy. Author: Sandeep Belgavi"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import policy  # noqa: E402


class RefusalFallbackPolicyTest(unittest.TestCase):
    def test_installed_version_is_the_pinned_one(self):
        import pydantic_ai

        self.assertEqual(pydantic_ai.__version__, "2.65.0")

    def test_default_sends_a_refusal_with_text_to_the_backup(self):
        r = policy.run_scenario(refusal_has_text=True)
        self.assertEqual(r["calls"], ["primary", "backup"])
        self.assertEqual(r["output"], policy.BACKUP_ANSWER)

    def test_default_sends_an_empty_refusal_to_the_backup(self):
        r = policy.run_scenario(refusal_has_text=False)
        self.assertEqual(r["calls"], ["primary", "backup"])
        self.assertIsNone(r["error"])

    def test_explicit_policy_matches_the_default(self):
        self.assertEqual(policy.run_scenario(True, policy.REFUSALS_FALL_BACK), policy.run_scenario(True))

    def test_refusals_stop_never_reaches_the_backup(self):
        for has_text in (True, False):
            with self.subTest(has_text=has_text):
                self.assertEqual(policy.run_scenario(has_text, policy.REFUSALS_STOP)["calls"], ["primary"])

    def test_refusals_stop_raises_on_an_empty_refusal(self):
        r = policy.run_scenario(False, policy.REFUSALS_STOP)
        self.assertEqual(r["error"], "ContentFilterError")

    def test_refusals_stop_returns_refusal_text_as_output(self):
        # The pre-2.65.0 behaviour: refusal text becomes the answer. Guard against it if
        # users must never see it as an answer.
        r = policy.run_scenario(True, policy.REFUSALS_STOP)
        self.assertEqual(r["output"], "I cannot help with that.")

    def test_quota_is_not_a_rate_limit(self):
        self.assertFalse(policy.quota_is_rate_limit())


if __name__ == "__main__":
    unittest.main()
