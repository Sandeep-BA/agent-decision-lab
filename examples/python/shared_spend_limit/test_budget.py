"""Author: Sandeep Belgavi. Tests for the shared spend limit example. Thread scheduling varies, so the
fleet tests assert invariants rather than exact totals; the gap demo is deterministic."""
import threading
import unittest

from budget import CheckThenSpend, FakeClient, SharedBudget, gap_demo, run_fleet


class SpendLimitTests(unittest.TestCase):
    def test_check_then_spend_lets_every_concurrent_call_through(self):
        r = gap_demo(limit=10000, runs=8)
        self.assertEqual(r['spent'], 33954)
        self.assertGreater(r['spent'], r['limit'])

    def test_reservations_never_exceed_the_limit_under_concurrency(self):
        for seed in (1, 2, 3, 4, 5):
            policy = SharedBudget(60000)
            r = run_fleet(policy, runs=16, seed=seed)
            self.assertEqual(r['over'], 0, r)
            self.assertLessEqual(policy.peak, 60000)
            self.assertEqual(policy.reserved, 0)

    def test_a_large_budget_completes_every_run_under_both_policies(self):
        for policy in (CheckThenSpend(10**7), SharedBudget(10**7)):
            r = run_fleet(policy)
            self.assertEqual(r['completed'], 12)

    def test_a_failed_call_keeps_its_hold(self):
        class Boom(FakeClient):
            def create(self, input_tokens, max_tokens):
                raise TimeoutError('provider timed out')
        policy = SharedBudget(20000)
        with self.assertRaises(TimeoutError):
            policy.step(Boom(1), 500, 8000)
        self.assertEqual(policy.settled, 8500)
        self.assertEqual(policy.reserved, 0)

    def test_a_refused_reservation_spends_nothing(self):
        policy = SharedBudget(5000)
        self.assertIsNone(policy.step(FakeClient(1), 500, 8000))
        self.assertEqual(policy.spent, 0)

    def test_output_is_cut_at_max_tokens(self):
        client = FakeClient(7, mean_output=50000)
        r = client.create(100, 2000)
        self.assertEqual(r.usage.output_tokens, 2000)
        self.assertEqual(r.stop_reason, 'max_tokens')


if __name__ == '__main__':
    unittest.main()
