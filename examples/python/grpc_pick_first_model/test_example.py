"""Author: Sandeep Belgavi. Tests for the pick_first first-pass timeline model."""
import json
import unittest
from pathlib import Path
from example import DELAY_MS, SCENARIOS, dedup, first_pass, interleave, main


class PickFirst(unittest.TestCase):
    def test_interleave_starts_with_first_family(self):
        order = [a["addr"] for a in interleave(SCENARIOS["ipv6 blackholed"])]
        self.assertEqual(order, ["[2001:db8::10]:443", "192.0.2.10:443", "[2001:db8::11]:443", "192.0.2.11:443"])

    def test_dedup_keeps_first_occurrence(self):
        self.assertEqual(len(dedup(SCENARIOS["first address refused, duplicates"])), 2)

    def test_serial_waits_for_each_timeout(self):
        r = first_pass(SCENARIOS["ipv6 blackholed"], False, 20_000)
        self.assertEqual((r["ready_ms"], r["address"], r["max_parallel"]), (40_030, "192.0.2.10:443", 1))

    def test_happy_eyeballs_starts_next_after_delay(self):
        r = first_pass(SCENARIOS["ipv6 blackholed"], True, 20_000)
        self.assertEqual((r["ready_ms"], r["address"]), (DELAY_MS + 30, "192.0.2.10:443"))
        self.assertEqual(r["max_parallel"], 2)

    def test_failure_moves_on_immediately(self):
        r = first_pass(SCENARIOS["first address refused, duplicates"], True, 20_000)
        self.assertEqual(r["ready_ms"], 42)

    def test_all_down_reports_transient_failure_once(self):
        for he in (False, True):
            r = first_pass(SCENARIOS["all down"], he, 20_000)
            self.assertEqual((r["state"], r["reresolution_requests"], r["failed_ms"]), ("TRANSIENT_FAILURE", 1, 20_003))

    def test_connect_timeout_is_an_input(self):
        self.assertEqual(first_pass(SCENARIOS["ipv6 blackholed"], False, 5_000)["ready_ms"], 10_030)

    def test_expected_file_matches(self):
        expected = json.loads(Path(__file__).with_name("expected.json").read_text(encoding="utf-8"))
        self.assertEqual(main(), expected)


if __name__ == "__main__":
    unittest.main()
