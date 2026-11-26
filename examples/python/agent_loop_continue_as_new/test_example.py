"""Author: Sandeep Belgavi. Tests for the agent-loop history estimate and continue-as-new state."""
import json
import unittest
from pathlib import Path
from example import (EVENT_LIMIT, SIZE_LIMIT, Turn, chain, effect_key, events_per_turn, first_limit,
                     main, mid_turn_boundary, transcript_growth)


class ContinueAsNew(unittest.TestCase):
    def test_event_count_per_turn(self):
        self.assertEqual(events_per_turn(Turn()), 19)
        self.assertEqual(events_per_turn(Turn(tools=0)), 10)

    def test_inline_transcript_hits_size_first(self):
        r = first_limit(Turn(), inline_transcript=True)
        self.assertEqual((r["turn"], r["limit"]), (112, "size"))
        self.assertGreaterEqual(r["bytes"], SIZE_LIMIT)
        self.assertEqual(r["first_warning"], {"turn": 50, "by": "size"})

    def test_reference_transcript_hits_events_first(self):
        r = first_limit(Turn(), inline_transcript=False)
        self.assertEqual((r["turn"], r["limit"]), (2695, "events"))
        self.assertGreaterEqual(r["events"], EVENT_LIMIT)
        self.assertEqual(r["first_warning"], {"turn": 539, "by": "events"})

    def test_quadratic_growth(self):
        small = first_limit(Turn(tool_result_bytes=1000), True)["turn"]
        large = first_limit(Turn(tool_result_bytes=12000), True)["turn"]
        self.assertGreater(small, large)

    def test_chain_keeps_every_run_far_below_limits(self):
        c = chain(Turn(), 500, 200)
        self.assertEqual([r["turns"] for r in c["runs"]], [[1, 200], [201, 400], [401, 500]])
        self.assertTrue(all(r["events"] < 10_240 for r in c["runs"]))
        self.assertEqual(c["effects_executed"], c["unique_effects"])
        self.assertEqual(c["carried_state_example"]["next_turn"], 501)

    def test_effect_keys_must_not_use_run_id(self):
        self.assertEqual(mid_turn_boundary("run_id")["refunds_sent_for_turn_200"], 2)
        self.assertEqual(mid_turn_boundary("case_turn")["refunds_sent_for_turn_200"], 1)
        self.assertEqual(effect_key("CASE-1", 3, "x"), "CASE-1:turn-3:x")

    def test_expected_file_matches(self):
        expected = json.loads(Path(__file__).with_name("expected.json").read_text(encoding="utf-8"))
        self.assertEqual(json.loads(json.dumps(main())), expected)
        self.assertEqual(transcript_growth(Turn()), 8300)


if __name__ == "__main__":
    unittest.main()
