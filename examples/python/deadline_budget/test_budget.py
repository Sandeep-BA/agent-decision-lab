# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

import unittest

from budget import BudgetExhausted, Deadline, run


class BudgetTest(unittest.TestCase):
    def test_for_hop_takes_the_smaller_of_cap_and_remaining(self):
        d = Deadline(10, lambda: 0)
        self.assertEqual(d.for_hop(cap=3, reserve=2, min_useful=1), 3)
        self.assertEqual(d.for_hop(cap=30, reserve=2, min_useful=1), 8)

    def test_exhausted_when_too_little_is_left(self):
        d = Deadline(1, lambda: 0)
        with self.assertRaises(BudgetExhausted):
            d.for_hop(cap=5, reserve=0.9, min_useful=0.5)

    def test_fixed_timeouts_overrun_the_deadline(self):
        r = run(policy="fixed")
        self.assertEqual((r["finished"], r["overrun"], r["ghost"], r["refunds"]), (29400, 9400, 12000, 2))
        self.assertFalse(r["delivered"])

    def test_propagated_deadline_delivers_in_time(self):
        r = run(policy="propagate")
        self.assertEqual((r["finished"], r["overrun"], r["refunds"], r["skipped"]), (19400, 0, 1, 1))
        self.assertTrue(r["delivered"])

    def test_cancellation_removes_ghost_work_and_the_refund(self):
        r = run(policy="propagate", cancel=True)
        self.assertEqual((r["ghost"], r["refunds"]), (0, 0))

    def test_idempotent_key_keeps_refunds_at_one_under_retries(self):
        self.assertEqual(run(policy="fixed", idempotent=True)["refunds"], 1)

    def test_fast_refund_finishes_both_ways(self):
        for policy in ("fixed", "propagate"):
            r = run(policy=policy, refund_ms=2000)
            self.assertEqual(r["overrun"], 0)
            self.assertEqual(r["refunds"], 1)

    def test_slow_final_model_uses_a_template(self):
        r = run(policy="propagate", model_ms=8000)
        self.assertTrue(r["fallback"])
        self.assertEqual(r["finished"], 20000)


if __name__ == "__main__":
    unittest.main()
