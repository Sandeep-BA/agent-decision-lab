"""Tests for the map step model. Author: Sandeep Belgavi."""
import unittest
from map_step import CASES, Item, crash_and_resume, ordered, run_map


def with_outcome(key, outcome):
    return [Item(i.key, i.duration, outcome if i.key == key else "ok") for i in CASES]


class MapStepTest(unittest.TestCase):
    def test_three_workers_all_ok(self):
        r = run_map(CASES, 3)
        self.assertEqual((r.status, r.finished_at, r.starts), ("completed", 19, 8))
        self.assertEqual(ordered(CASES, r), ["ok"] * 8)

    def test_one_worker_is_the_sum(self):
        self.assertEqual(run_map(CASES, 1).finished_at, sum(i.duration for i in CASES))

    def test_unbounded_workers_is_the_longest_item(self):
        self.assertEqual(run_map(CASES, 8).finished_at, 9)

    def test_fail_fast_cancels_running_items(self):
        items = with_outcome("CASE-5104", "fail")
        r = run_map(items, 3, "fail_fast")
        self.assertEqual((r.status, r.finished_at, r.wasted_seconds), ("failed", 12, 6))
        self.assertEqual(r.cancelled, ["CASE-5106", "CASE-5108"])
        self.assertEqual(ordered(items, r), ["ok", "ok", "ok", "error", "ok", "cancelled", "ok", "cancelled"])

    def test_collect_keeps_going(self):
        items = with_outcome("CASE-5104", "fail")
        r = run_map(items, 3, "collect")
        self.assertEqual((r.status, r.finished_at), ("completed with errors", 19))
        self.assertEqual(ordered(items, r).count("ok"), 7)

    def test_resume_with_checkpoints_runs_only_lost_items(self):
        first, second = crash_and_resume(CASES, 3, "fail_fast", True, 12)
        self.assertEqual(first.wasted_seconds, 6)
        self.assertEqual((second.starts, second.finished_at, first.starts + second.starts), (2, 20, 10))

    def test_resume_without_checkpoints_runs_everything_again(self):
        first, second = crash_and_resume(CASES, 3, "fail_fast", False, 12)
        self.assertEqual((second.starts, second.finished_at, first.starts + second.starts), (8, 31, 16))

    def test_input_request_stops_queued_items(self):
        items = with_outcome("CASE-5103", "input")
        r = run_map(items, 3)
        self.assertEqual((r.status, r.finished_at), ("paused for input", 7))
        self.assertEqual(ordered(items, r)[:3], ["ok", "ok", "needs input"])
        self.assertEqual(ordered(items, r)[3:], ["not run"] * 5)

    def test_rejects_zero_workers(self):
        with self.assertRaises(ValueError):
            run_map(CASES, 0)


if __name__ == "__main__":
    unittest.main()
