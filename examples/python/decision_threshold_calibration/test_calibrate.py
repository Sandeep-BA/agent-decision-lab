"""Author: Sandeep Belgavi. Tests for the offline Decisions threshold example (no provider calls)."""
import json
import unittest
from pathlib import Path

import calibrate as c

HERE = Path(__file__).resolve().parent


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.items = c.make_fixture()

    def test_fixture_is_deterministic(self):
        self.assertEqual(self.items, c.make_fixture())
        self.assertEqual(len(self.items), 200)
        self.assertEqual(sum(x["label"] for x in self.items), 98)

    def test_reliability_shows_overconfidence_at_the_top(self):
        top = c.reliability_table(self.items)[-1]
        self.assertEqual(top["count"], 85)
        self.assertGreater(top["mean_predicted"], top["observed"])     # 0.962 predicted, 0.894 observed

    def test_band_beats_a_single_cut(self):
        naive = c.band_cost(self.items, 0.5, 0.5 + 1e-9, c.COST)
        band = c.choose_band(self.items, c.COST)
        self.assertEqual((naive["wrong_approve"], naive["wrong_deny"], naive["cost"]), (20, 13, 1125))
        self.assertEqual((band["low"], band["high"]), (0.1, 0.9))
        self.assertEqual((band["wrong_approve"], band["wrong_deny"], band["reviewed"], band["cost"]), (5, 2, 54, 412))

    def test_holdout(self):
        fitted = c.choose_band(self.items[:100], c.COST)
        self.assertEqual((fitted["low"], fitted["high"]), (0.05, 1.0))   # 100 labels: never auto-approve
        held = c.band_cost(self.items[100:], fitted["low"], fitted["high"], c.COST)
        self.assertEqual(held["cost"], 244)
        self.assertEqual(c.band_cost(self.items[100:], 0.5, 0.5 + 1e-9, c.COST)["cost"], 720)

    def test_score_threshold_uses_probabilities_not_the_rounded_score(self):
        decision = json.loads((HERE / "fixtures" / "decision_shaped.json").read_text(encoding="utf-8"))
        severity = next(a for a in decision["answers"] if a["type"] == "score")
        self.assertEqual(severity["score"], 1.6)                       # rounds to "high" (2) ...
        self.assertAlmostEqual(c.at_least(severity, 2), 0.6)           # ... P(high or worse) is 0.6

    def test_refusal_and_low_probability_choice_go_to_review(self):
        decision = json.loads((HERE / "fixtures" / "decision_shaped.json").read_text(encoding="utf-8"))
        actions = c.parse_answers(decision, {"low": 0.1, "high": 0.9})
        self.assertEqual(actions, {"duplicate_charge": "approve", "department": "review: low probability",
                                   "severity": "page on-call", "fraud_suspected": "review: refused"})


if __name__ == "__main__":
    unittest.main()
