"""Tests for the paged-experts simulator. Author: Sandeep Belgavi."""
import json
import pathlib
import unittest

from paged import LRUSlots, simulate

HERE = pathlib.Path(__file__).resolve().parent
CFG = json.loads((HERE / "fixtures" / "qwen3_30b_a3b_int4.json").read_text(encoding="utf-8"))
BASE = CFG["base"]


class Residency(unittest.TestCase):
    def test_slots_start_with_low_ids_and_evict_lru_outside_the_wave(self):
        s = LRUSlots(4)
        self.assertEqual(s.place([0, 1]), 0)            # 2 and 3 are now least recently used
        self.assertEqual(s.place([1, 9]), 1)            # 9 evicts expert 2
        self.assertNotIn(2, s.resident)
        self.assertIn(0, s.resident)

    def test_waves_put_resident_experts_first(self):
        s = LRUSlots(3)
        res = s.plan([5, 0, 6, 1, 7])
        self.assertEqual((res["hits"], res["loads"], res["waves"]), (2, 3, 2))

    def test_empty_step_still_gets_one_wave(self):
        self.assertEqual(LRUSlots(2).plan([])["waves"], 1)


class Arithmetic(unittest.TestCase):
    def test_documented_sizes(self):
        r = simulate(BASE)
        self.assertEqual((r["gpu_expert_gb"], r["pinned_host_gb"]), (10.73, 14.93))
        self.assertEqual(r["capture_limit_requests"], 11)
        self.assertAlmostEqual(r["prefill_paged_gb"], 4.2, places=1)   # 36 non-resident experts x 48 layers

    def test_all_resident_never_pages(self):
        r = simulate({**BASE, "resident": 128})
        self.assertEqual((r["decode_miss_rate_pct"], r["prefill_paged_gb"]), (0.0, 0.0))

    def test_uniform_routing_misses_about_one_minus_k_over_e(self):
        r = simulate({**BASE, "locality": 0.0, "skew": 0.0, "decode_steps": 1000})
        self.assertAlmostEqual(r["decode_miss_rate_pct"], 100 * (1 - 92 / 128), delta=3)

    def test_locality_lowers_misses(self):
        self.assertLess(simulate(BASE)["decode_miss_rate_pct"], simulate({**BASE, "locality": 0.0})["decode_miss_rate_pct"])

    def test_small_k_loses_capture_and_needs_waves(self):
        r = simulate({**BASE, "resident": 26, "batch": 4})
        self.assertFalse(r["decode_captured"])
        self.assertGreater(r["decode_steps_with_several_waves"], 0)

    def test_bandwidth_halves_time(self):
        a, b = simulate(BASE), simulate({**BASE, "gbps": 25})
        self.assertAlmostEqual(b["transfer_ms_per_decode_step"], 2 * a["transfer_ms_per_decode_step"], delta=0.02)

    def test_invalid_k(self):
        with self.assertRaises(ValueError):
            simulate({**BASE, "resident": 4})

    def test_expected_output(self):
        want = json.loads((HERE / "expected_output.json").read_text(encoding="utf-8"))
        got = {n: simulate({**BASE, **o}) for n, o in CFG["runs"].items()}
        self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()
