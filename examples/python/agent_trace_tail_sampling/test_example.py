"""Author: Sandeep Belgavi. Tests for outcome-based tail sampling of segmented agent runs."""
import json
import unittest
from pathlib import Path
from example import bucket, evaluate, keep, make_runs, memory_traces, main


class TailSampling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs = make_runs()
        cls.by = {p: evaluate(p, cls.runs) for p in ("head", "tail", "tail-tid", "tail+pause")}

    def test_bucket_is_stable_and_in_range(self):
        self.assertEqual(bucket("CASE-1"), bucket("CASE-1"))
        self.assertTrue(all(0 <= bucket(f"x{i}") < 100 for i in range(500)))

    def test_tail_keeps_every_error_and_write(self):
        for p in ("tail", "tail-tid", "tail+pause"):
            r = self.by[p]
            self.assertEqual(r["error_or_write_segments_kept"], r["error_or_write_segments"])
            self.assertEqual(r["approval_runs_complete"], r["approval_runs"])

    def test_head_loses_most_signal(self):
        r = self.by["head"]
        self.assertLess(r["error_or_write_segments_kept"], 0.1 * r["error_or_write_segments"])

    def test_run_bucket_keeps_routine_runs_whole(self):
        self.assertEqual(self.by["tail"]["routine_runs_kept_partially"], 0)
        self.assertGreater(self.by["tail-tid"]["routine_runs_kept_partially"], 0)

    def test_pause_rule_removes_missing_context(self):
        self.assertGreater(self.by["tail"]["kept_error_or_write_segments_missing_an_earlier_segment"], 0)
        self.assertEqual(self.by["tail+pause"]["kept_error_or_write_segments_missing_an_earlier_segment"], 0)

    def test_errors_always_win_over_bucket(self):
        run = {"run_id": "CASE-1", "segments": []}
        seg = {"trace_id": "t", "error": True, "writes": 0, "approval_in_run": False}
        self.assertTrue(keep("tail", run, seg))

    def test_memory_scales_with_decision_wait(self):
        self.assertAlmostEqual(memory_traces(self.runs, 60), 2 * memory_traces(self.runs, 30), delta=1)

    def test_expected_file_matches(self):
        expected = json.loads(Path(__file__).with_name("expected.json").read_text(encoding="utf-8"))
        self.assertEqual(main(), expected)


if __name__ == "__main__":
    unittest.main()
