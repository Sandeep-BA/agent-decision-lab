"""Tests for the change budget. Standard library unittest only.

Author: Sandeep Belgavi.
"""
import unittest

from budget import ChangeBudget, run_agent, runaway_deletions


class BudgetTests(unittest.TestCase):
    def test_runaway_halts_before_exceeding_the_cap(self):
        b = ChangeBudget(limits={"rows": 500, "customers": 50})
        res = run_agent(b, runaway_deletions(120, 20), auto_approve=True)
        self.assertTrue(res.halted)
        self.assertEqual(res.committed, 4)        # 4*120=480 committed; the 5th (600) halts
        self.assertLessEqual(res.spent["rows"], 500)

    def test_approve_threshold_routes_to_a_human(self):
        b = ChangeBudget(limits={"rows": 500, "customers": 50})
        res = run_agent(b, runaway_deletions(120, 20), auto_approve=False)
        self.assertFalse(res.halted)
        self.assertEqual(res.approvals, 1)
        self.assertEqual(res.committed, 3)        # stops at the first 'approve' (480 > 400)

    def test_blast_radius_not_request_count(self):
        b = ChangeBudget(limits={"rows": 500})
        # One statement that changes 1000 rows halts immediately, even though it is one request.
        self.assertEqual(b.check({"rows": 1000}), "halt")
        # A thousand one-row changes are individually fine until the total crosses the cap.
        res = run_agent(b, [("r", {"rows": 1}) for _ in range(1000)], auto_approve=True)
        self.assertTrue(res.halted)
        self.assertEqual(res.committed, 500)

    def test_customers_dimension_binds_first(self):
        b = ChangeBudget(limits={"rows": 100000, "customers": 10})
        res = run_agent(b, [("c", {"rows": 1, "customers": 1}) for _ in range(50)], auto_approve=True)
        self.assertTrue(res.halted)
        self.assertEqual(res.spent["customers"], 10)

    def test_everything_within_budget_commits(self):
        b = ChangeBudget(limits={"rows": 500})
        res = run_agent(b, [("r", {"rows": 10}) for _ in range(5)], auto_approve=True)
        self.assertFalse(res.halted)
        self.assertEqual(res.committed, 5)
        self.assertEqual(res.spent["rows"], 50)


if __name__ == "__main__":
    unittest.main()
