"""Author: Sandeep Belgavi. Tests for the topology spread model."""
import unittest
from example import demo, place


class TopologySpread(unittest.TestCase):
    def test_documented_example_global_min(self):
        # Docs: zones with 2, 2 and 1 matching pods, maxSkew 1 -> global minimum 1.
        r = place(1, {"a": 9, "b": 9, "c": 9}, existing={"a": 2, "b": 2, "c": 1})
        self.assertEqual(r["trace"][0]["global_min"], 1)
        self.assertEqual(r["trace"][0]["placed"], "c")
        self.assertEqual([o["feasible"] for o in r["trace"][0]["options"]], [False, False, True])

    def test_scenarios(self):
        d = demo()
        self.assertEqual(d["healthy_3_zones"]["counts"], {"zone-a": 2, "zone-b": 2, "zone-c": 2})
        self.assertEqual(d["zone_c_lost"]["pending"], 0)
        self.assertEqual(d["zone_c_lost_min_domains_3"]["pending"], 2)
        self.assertEqual(d["zone_c_lost_b_full_DoNotSchedule"]["pending"], 1)
        self.assertEqual(d["zone_c_lost_b_full_ScheduleAnyway"]["pending"], 0)
        self.assertEqual(d["zone_c_nodes_tainted_policy_Ignore"]["pending"], 2)
        self.assertEqual(d["zone_c_nodes_tainted_policy_Honor"]["pending"], 0)

    def test_skew_never_exceeds_max_under_do_not_schedule(self):
        for skew in (1, 2, 3):
            r = place(17, {"a": 20, "b": 20, "c": 20}, max_skew=skew)
            c = r["counts"].values()
            self.assertLessEqual(max(c) - min(c), skew)

    def test_invalid_arguments(self):
        for kwargs in ({"max_skew": 0}, {"min_domains": 0}, {"when": "Maybe"}, {"taints_policy": "Sometimes"}):
            with self.assertRaises(ValueError):
                place(1, {"a": 1}, **kwargs)


if __name__ == "__main__":
    unittest.main()
