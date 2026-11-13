"""Tests for the steering mailbox model. Author: Sandeep Belgavi."""
import unittest
from steering import Turn, run

PLAN = ["sample", "tool:lookup_order", "tool:draft_refund", "sample", "final"]


class SteeringTest(unittest.TestCase):
    def test_steer_before_tools_drops_stale_calls(self):
        t = run(Turn(PLAN), {1: "Only CASE-7031"})
        self.assertEqual(t.executed, ["sample", "sample", "final"])
        self.assertEqual(t.delivered, ["Only CASE-7031"])

    def test_steer_during_tool_waits_for_the_boundary(self):
        t = run(Turn(PLAN), {2: "Only CASE-7031"})
        self.assertEqual(t.executed, ["sample", "tool:lookup_order", "sample", "final"])

    def test_no_steer_runs_the_plan(self):
        self.assertEqual(run(Turn(PLAN)).executed, PLAN)

    def test_check_then_close_loses_a_steer(self):
        t = Turn(["sample", "final"], atomic_close=False)
        t.on_flush = lambda tt: tt.steer("Also mention the return window")
        run(t)
        self.assertEqual((t.delivered, t.lost), ([], ["Also mention the return window"]))

    def test_atomic_close_delivers_it_in_the_same_turn(self):
        t = Turn(["sample", "final"], atomic_close=True)
        t.on_flush = lambda tt: tt.steer("Also mention the return window")
        run(t)
        self.assertEqual((t.delivered, t.lost), (["Also mention the return window"], []))
        self.assertEqual(t.executed, ["sample", "final", "sample", "final"])
        self.assertEqual(t.state, "done")

    def test_after_close_input_goes_to_next_task(self):
        t = run(Turn(["sample", "final"]))
        self.assertEqual(t.steer("Tomorrow, CASE-7032"), "queued")
        self.assertEqual((t.next_task, t.delivered), (["Tomorrow, CASE-7032"], []))


if __name__ == "__main__":
    unittest.main()
