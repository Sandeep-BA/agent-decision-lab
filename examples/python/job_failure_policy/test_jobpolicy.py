"""Tests for the Job failure-policy replay; they check the table in the article. Author: Sandeep Belgavi."""
import json
import pathlib
import unittest

from jobpolicy import ARTICLE_POLICY, replay, run, validate

HERE = pathlib.Path(__file__).resolve().parent
FIX = json.loads((HERE / "fixtures" / "nights.json").read_text(encoding="utf-8"))
NIGHT = ["evict", "evict", "exit1", "ok"]


class ArticleTable(unittest.TestCase):
    def test_rows(self):
        r = {x["name"]: x for x in run(FIX)}
        self.assertEqual((r["Default, backoffLimit 6"]["counted"], r["Default, backoffLimit 6"]["pods"], r["Default, backoffLimit 6"]["result"]), (3, 4, "succeeded"))
        self.assertEqual((r["Default, backoffLimit 2"]["counted"], r["Default, backoffLimit 2"]["pods"], r["Default, backoffLimit 2"]["result"]), (3, 3, "failed"))
        self.assertEqual((r["Article policy, backoffLimit 3"]["counted"], r["Article policy, backoffLimit 3"]["pods"], r["Article policy, backoffLimit 3"]["result"]), (1, 4, "succeeded"))
        x = r["Article policy, malformed feed first"]
        self.assertEqual((x["pods"], x["result"], x["reason"]), (1, "failed", "FailJob rule"))

    def test_default_malformed_feed_waits_630_seconds(self):
        x = {x["name"]: x for x in run(FIX)}["Default, malformed feed"]
        self.assertEqual((x["pods"], x["backoff"]), (7, 630))

    def test_oom_is_counted_and_pressure_is_ignored(self):
        r = {x["name"]: x for x in run(FIX)}
        self.assertEqual((r["Article policy, OOM every time"]["counted"], r["Article policy, OOM every time"]["result"]), (4, "failed"))
        self.assertEqual((r["Article policy, node pressure, no deadline"]["result"], r["Article policy, node pressure, no deadline"]["counted"]), ("active", 0))
        x = r["Article policy, node pressure, deadline 3600 s"]
        self.assertEqual((x["result"], x["reason"], x["t"]), ("failed", "DeadlineExceeded", 3600))


class Validation(unittest.TestCase):
    def test_zero_not_allowed_with_in(self):
        with self.assertRaises(ValueError):
            validate({"rules": [{"action": "FailJob", "onExitCodes": {"operator": "In", "values": [0, 3]}}]})

    def test_rule_needs_exactly_one_matcher(self):
        with self.assertRaises(ValueError):
            validate({"rules": [{"action": "Ignore"}]})

    def test_first_match_wins(self):
        policy = {"rules": [{"action": "Ignore", "onPodConditions": [{"type": "DisruptionTarget"}]},
                            {"action": "FailJob", "onExitCodes": {"operator": "In", "values": [143]}}]}
        self.assertEqual(replay({"backoffLimit": 0, "podFailurePolicy": policy}, NIGHT)["counted"], 1)
        swapped = {"rules": list(reversed(policy["rules"]))}
        self.assertEqual(replay({"backoffLimit": 0, "podFailurePolicy": swapped}, NIGHT)["reason"], "FailJob rule")

    def test_not_in_operator(self):
        policy = {"rules": [{"action": "FailJob", "onExitCodes": {"operator": "NotIn", "values": [1, 143]}}]}
        self.assertEqual(replay({"podFailurePolicy": policy}, ["exit1", "oom"])["reason"], "FailJob rule")

    def test_expected_output(self):
        self.assertEqual(run(FIX), json.loads((HERE / "expected_output.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
