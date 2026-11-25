"""Author: Sandeep Belgavi. Behavioural tests for state-scoped tool exposure."""
import unittest
from example import ALLOWED, TOOLS, TRANSITIONS, Case, demo, execute, visible_tools


class StateScopedTools(unittest.TestCase):
    def test_allowlist_names_only_known_tools(self):
        for state, tools in ALLOWED.items():
            self.assertTrue(tools <= set(TOOLS), state)

    def test_transitions_target_known_states(self):
        self.assertTrue(set(TRANSITIONS.values()) <= set(ALLOWED))

    def test_refund_not_visible_before_verification(self):
        self.assertNotIn("issue_refund", visible_tools(Case("CASE-1", "awaiting_verification")))

    def test_execution_rechecks_state(self):
        case = Case("CASE-2", "awaiting_verification")
        self.assertEqual(execute(case, "issue_refund", 0), "rejected_not_allowed_in_state")
        self.assertEqual(case.state, "awaiting_verification")
        self.assertEqual(case.log, [])

    def test_unknown_tool_and_state(self):
        self.assertEqual(execute(Case("CASE-3", "verified"), "delete_account", 0), "rejected_unknown_tool")
        with self.assertRaises(ValueError):
            visible_tools(Case("CASE-4", "escalated"))

    def test_stale_listing_cannot_refund_twice(self):
        result = demo()
        calls = [t for t in result["trace"] if "call" in t]
        self.assertEqual([c["result"] for c in calls],
                         ["rejected_not_allowed_in_state", "applied", "applied", "rejected_not_allowed_in_state"])
        self.assertEqual(result["final_state"], "refunded")
        self.assertEqual(result["revision"], 2)

    def test_stale_revision_blocks_write_in_same_state(self):
        case = Case("CASE-5", "verified", revision=3)
        self.assertEqual(execute(case, "issue_refund", 2), "rejected_stale_listing")
        self.assertEqual(execute(case, "lookup_order", 2), "applied")  # reads tolerate staleness

    def test_closed_case_exposes_nothing(self):
        self.assertEqual(visible_tools(Case("CASE-6", "closed")), [])


if __name__ == "__main__":
    unittest.main()
