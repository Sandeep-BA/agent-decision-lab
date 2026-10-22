"""Tests for the prompt-cache audit example. Author: Sandeep Belgavi."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cache_audit import Block, Request, first_divergence, loop, simulate  # noqa: E402


class DivergenceTests(unittest.TestCase):
    def test_appending_blocks_is_not_a_divergence(self):
        a = [Block("system", 10, "x")]
        self.assertIsNone(first_divergence(a, a + [Block("user1", 5, "hi")]))

    def test_reordered_tools_diverge_at_the_first_block(self):
        a, b = Block("tool:a", 1, "a"), Block("tool:b", 1, "b")
        self.assertEqual(first_divergence([a, b], [b, a]), 0)


class SimulationTests(unittest.TestCase):
    def test_stable_prefix(self):
        r = simulate(loop("stable"))
        self.assertEqual((r["hit_rate_pct"], r["cost_vs_uncached_pct"]), (85.9, 26.2))

    def test_timestamp_in_the_system_prompt_never_hits(self):
        r = simulate(loop("timestamp"))
        self.assertEqual(r["totals"]["read"], 0)
        self.assertEqual(r["cost_vs_uncached_pct"], 125.0)   # every request pays the write premium

    def test_tool_reorder_costs_one_full_rewrite(self):
        rows = simulate(loop("tool_order"))["rows"]
        self.assertEqual(rows[4]["read"], 0)
        self.assertEqual(rows[4]["diverged_at"], "0:tool:get_order")
        self.assertEqual(rows[5]["read"], 5800)

    def test_pause_longer_than_the_ttl_expires_the_entry(self):
        short = simulate(loop("approval_pause"), ttl=300)
        long = simulate(loop("approval_pause"), ttl=3600)
        self.assertEqual(short["rows"][5]["read"], 0)
        self.assertEqual(short["hit_rate_pct"], 76.4)
        self.assertEqual(long["hit_rate_pct"], 85.9)

    def test_lookback_window_limits_reads(self):
        blocks = [Block(f"b{i}", 100, str(i)) for i in range(40)]
        first = Request(0, blocks[:15], breakpoints=[14])
        far = Request(1, blocks[:40], breakpoints=[39])       # 25 blocks past the last write
        near = Request(1, blocks[:40], breakpoints=[14, 39])  # a second breakpoint at the old write
        self.assertEqual(simulate([first, far], min_tokens=0)["rows"][1]["read"], 0)
        self.assertEqual(simulate([first, near], min_tokens=0)["rows"][1]["read"], 1500)

    def test_prefix_below_the_minimum_is_not_cached(self):
        reqs = [Request(0, [Block("s", 500, "x")], [0]), Request(1, [Block("s", 500, "x")], [0])]
        self.assertEqual(simulate(reqs, min_tokens=1024)["totals"]["read"], 0)


if __name__ == "__main__":
    unittest.main()
