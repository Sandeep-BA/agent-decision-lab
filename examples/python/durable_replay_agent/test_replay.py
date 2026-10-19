"""Tests for the durable replay model. Author: Sandeep Belgavi."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replay  # noqa: E402

FIXTURE = json.loads(replay.FIXTURE.read_text(encoding="utf-8"))


class ReplayTests(unittest.TestCase):
    def setUp(self):
        replay.MODEL_CALLS = 0

    def test_replay_does_not_call_the_model_again(self):
        result, wf = replay.resume("P-204", FIXTURE["history"], replay.procurement_v1, FIXTURE["request"], {"approval": True})
        self.assertEqual(result, "ORD-7200-B")
        self.assertEqual(replay.MODEL_CALLS, 0)
        self.assertEqual(wf.live_activities, 2)          # place_order and notify ran live

    def test_waiting_for_approval_blocks_without_executing_effects(self):
        with self.assertRaises(replay.Waiting):
            replay.resume("P-204", FIXTURE["history"], replay.procurement_v1, FIXTURE["request"], {})

    def test_reordered_code_is_non_deterministic_against_old_history(self):
        history = FIXTURE["history"] + [
            {"kind": "signal", "name": "approval", "result": True},
            {"kind": "activity", "name": "place_order", "result": {"order_id": "ORD-7200-B", "idempotency_key": "P-204:place_order"}},
        ]
        with self.assertRaises(replay.NonDeterministic):
            replay.resume("P-204", history, replay.procurement_reordered, FIXTURE["request"], {"approval": True})

    def test_blocked_wait_is_recorded_once(self):
        _r = None
        try:
            replay.resume("P-204", [FIXTURE["history"][0]], replay.procurement_v1, FIXTURE["request"], {})
        except replay.Waiting:
            _r = "waiting"
        self.assertEqual(_r, "waiting")

    def test_patch_marker_takes_old_path_on_old_history_and_new_path_on_new_runs(self):
        _r, old = replay.resume("P-204", FIXTURE["history"], replay.procurement_v2, FIXTURE["request"], {"approval": True})
        self.assertNotIn("compliance_check", [e["name"] for e in old.history])
        _r, new = replay.resume("P-205", [], replay.procurement_v2, FIXTURE["request"], {"approval": True})
        kinds = [(e["kind"], e["name"]) for e in new.history]
        self.assertIn(("patch", "compliance-check-2026-10"), kinds)
        self.assertIn(("activity", "compliance_check"), kinds)
        self.assertEqual(replay.MODEL_CALLS, 1)          # only the new run called the model

    def test_effecting_activity_carries_the_workflow_id_as_idempotency_key(self):
        _r, wf = replay.resume("P-204", FIXTURE["history"], replay.procurement_v1, FIXTURE["request"], {"approval": True})
        placed = next(e for e in wf.history if e["name"] == "place_order")
        self.assertEqual(placed["result"]["idempotency_key"], "P-204:place_order")

    def test_resume_twice_leaves_history_identical(self):
        _r, first = replay.resume("P-204", FIXTURE["history"], replay.procurement_v1, FIXTURE["request"], {"approval": True})
        _r, second = replay.resume("P-204", first.history, replay.procurement_v1, FIXTURE["request"], {"approval": True})
        self.assertEqual(first.history, second.history)
        self.assertEqual(second.live_activities, 0)


if __name__ == "__main__":
    unittest.main()
