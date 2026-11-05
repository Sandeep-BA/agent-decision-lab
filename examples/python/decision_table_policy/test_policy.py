"""Tests for the decision-table companion. Author: Sandeep Belgavi."""
import json
import pathlib
import unittest
from datetime import date

from policy import RULES_V6, RULES_V7, check_table, diff_versions, evaluate, run

HERE = pathlib.Path(__file__).resolve().parent
CASES = json.loads((HERE / "fixtures" / "cases.json").read_text(encoding="utf-8"))


class Evaluate(unittest.TestCase):
    def test_article_cases(self):
        out = {c["name"].split(":")[0]: c for c in run(CASES)["cases"]}
        self.assertEqual((out["Geetha"]["outcome"], out["Geetha"]["rule"]), ("refund", "R-1"))
        self.assertEqual((out["Jenya"]["outcome"], out["Jenya"]["rule"]), ("refund", "R-3"))
        self.assertEqual(out["Dinky"]["outcome"], "store_credit")
        self.assertEqual((out["Hansini"]["outcome"], out["Hansini"]["rule"]), ("refuse", "R-5"))

    def test_version_selected_by_delivery_date(self):
        out = {c["name"].split(":")[0]: c for c in run(CASES)["cases"]}
        self.assertEqual((out["Tanishka"]["version"], out["Tanishka"]["outcome"]), ("v6", "refuse"))
        self.assertEqual(out["Order delivered before any policy version"]["outcome"], "escalate")
        self.assertEqual(evaluate({"damaged": False, "sale": False, "member": True, "days": 40}, date(2026, 9, 1))["outcome"], "refund")

    def test_unique_policy_rejects_overlap(self):
        with self.assertRaises(ValueError):
            evaluate({"damaged": True, "sale": False, "member": False, "days": 5}, date(2026, 10, 1), hit_policy="UNIQUE")


class Checks(unittest.TestCase):
    def test_v7_has_no_gaps_and_only_catch_all_overlaps(self):
        chk = check_table(RULES_V7)
        self.assertEqual(chk["gaps"], [])
        self.assertEqual(chk["overlaps"], [("R-1", "R-5"), ("R-2", "R-5"), ("R-3", "R-5"), ("R-4", "R-5")])
        self.assertEqual(chk["unreachable"], [])

    def test_removing_catch_all_creates_gaps(self):
        gaps = check_table(RULES_V7[:-1])["gaps"]
        self.assertTrue(any(g["damaged"] and g["days"] == 91 for g in gaps))
        self.assertTrue(any(not g["damaged"] and g["days"] == 46 for g in gaps))

    def test_shadowed_rule_is_unreachable(self):
        shadowed = [RULES_V7[-1]] + RULES_V7[:-1]  # catch-all first under FIRST hides every other row
        self.assertEqual(check_table(shadowed)["unreachable"], ["R-1", "R-2", "R-3", "R-4"])

    def test_version_diff_lists_changed_outcomes(self):
        changes = diff_versions(RULES_V6, RULES_V7)
        self.assertTrue(changes)
        self.assertTrue(all(c["new_rule"] in ("R-2", "R-3") for c in changes))

    def test_expected_output(self):
        self.assertEqual(run(CASES), json.loads((HERE / "expected_output.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
