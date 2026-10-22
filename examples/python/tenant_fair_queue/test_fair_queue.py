"""Tests for the tenant fair queue example. Author: Sandeep Belgavi."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fair_queue import AgentBudget, Call, FairAdmission, FifoAdmission, simulate  # noqa: E402


class AdmissionTests(unittest.TestCase):
    def test_fair_queue_refuses_only_the_tenant_that_is_full(self):
        adm = FairAdmission(["A", "D"], limit_per_tenant=2)
        self.assertTrue(adm.offer(Call("D", 0)))
        self.assertTrue(adm.offer(Call("D", 0)))
        self.assertFalse(adm.offer(Call("D", 0)))   # D's own queue is full
        self.assertTrue(adm.offer(Call("A", 0)))    # A is unaffected

    def test_fifo_lets_one_tenant_fill_the_shared_queue(self):
        adm = FifoAdmission(limit=2)
        adm.offer(Call("D", 0))
        adm.offer(Call("D", 0))
        self.assertFalse(adm.offer(Call("A", 0)))

    def test_round_robin_alternates_between_backlogged_tenants(self):
        adm = FairAdmission(["A", "D"], limit_per_tenant=10)
        for _ in range(5):
            adm.offer(Call("D", 0))
        adm.offer(Call("A", 0))
        order = [adm.take().tenant for _ in range(3)]
        self.assertEqual(order, ["A", "D", "D"])

    def test_expiry_removes_calls_that_waited_too_long(self):
        adm = FairAdmission(["A"], limit_per_tenant=10)
        adm.offer(Call("A", 0))
        adm.offer(Call("A", 150))
        gone = adm.expire(now=200, max_wait=200)
        self.assertEqual(len(gone), 1)
        self.assertEqual(len(adm), 1)

    def test_budget_refuses_calls_beyond_the_bucket_and_rounds(self):
        budget = AgentBudget(per_second=2, max_rounds=1)
        self.assertTrue(budget.allow(Call("D", 0)))
        self.assertTrue(budget.allow(Call("D", 0)))
        self.assertFalse(budget.allow(Call("D", 0)))
        self.assertFalse(AgentBudget(per_second=0, max_rounds=1).allow(Call("D", 0, round=2)))


class ScenarioTests(unittest.TestCase):
    """The figures quoted in the article and README, from the default scenario."""

    def test_fifo_with_replans_hurts_ordinary_tenants(self):
        r = simulate("fifo")
        self.assertEqual(r["ordinary_served_pct"], 84.2)
        self.assertEqual(r["worst_ordinary_pct"], 76.7)
        self.assertEqual(r["tenants"]["D"]["offered"], 14092)
        self.assertEqual(r["tenants"]["D"]["replans"], 11852)

    def test_replans_are_part_of_the_damage(self):
        r = simulate("fifo", replan=0)
        self.assertEqual(r["ordinary_served_pct"], 88.5)
        self.assertEqual(r["tenants"]["D"]["offered"], 2240)

    def test_fair_queues_protect_ordinary_tenants_but_not_the_agent_from_itself(self):
        r = simulate("fair")
        self.assertEqual(r["ordinary_served_pct"], 100.0)
        self.assertEqual(r["tenants"]["D"]["replans"], 22632)

    def test_agent_budget_removes_the_amplification_at_the_source(self):
        r = simulate("fifo", budget=10)
        self.assertEqual(r["ordinary_served_pct"], 100.0)
        self.assertEqual(r["tenants"]["D"]["replans"], 0)
        self.assertEqual(r["tenants"]["D"]["held"], 1191)

    def test_deterministic(self):
        self.assertEqual(simulate("fair", seconds=20), simulate("fair", seconds=20))


if __name__ == "__main__":
    unittest.main()
