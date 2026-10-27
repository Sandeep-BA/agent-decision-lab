"""Tests for the bitemporal memory example; they follow the worked example in the guide. Author: Sandeep Belgavi."""
import json
import unittest
from pathlib import Path

from memory import believed, erase, learn, open_memory, record_conflict, replay

HERE = Path(__file__).resolve().parent
S, A = "customer-88", "shipping_address"


class Bitemporal(unittest.TestCase):
    def setUp(self):
        self.db = replay(json.loads((HERE / "fixtures" / "events.json").read_text(encoding="utf-8")))

    def test_three_rows_and_nothing_overwritten(self):
        rows = self.db.execute("SELECT value, valid_from, valid_to, recorded_from, recorded_to, source "
                               "FROM memory ORDER BY rowid").fetchall()
        self.assertEqual(rows, [
            ("4 Hill Street", "2024-02-01", None, "2024-02-01", "2026-10-10", "account signup"),
            ("4 Hill Street", "2024-02-01", "2026-10-03", "2026-10-10", None, "CASE-5120"),
            ("12 Lake Road", "2026-10-03", None, "2026-10-10", None, "CASE-5120")])

    def test_current_belief(self):
        self.assertEqual(believed(self.db, S, A, "2026-10-27", "2026-10-27"), [("12 Lake Road", "CASE-5120")])

    def test_what_applied_to_the_order_of_5_october(self):
        self.assertEqual(believed(self.db, S, A, "2026-10-05", "2026-10-27"), [("12 Lake Road", "CASE-5120")])

    def test_what_the_agent_believed_on_7_october(self):
        self.assertEqual(believed(self.db, S, A, "2026-10-07", "2026-10-07"), [("4 Hill Street", "account signup")])

    def test_correction_keeps_the_valid_period(self):
        learn(self.db, S, A, "12 Lake Rd, Flat 2", "2026-10-03", "2026-10-12", "CASE-5133")
        self.assertEqual(believed(self.db, S, A, "2026-10-05", "2026-10-12"), [("12 Lake Rd, Flat 2", "CASE-5133")])
        self.assertEqual(believed(self.db, S, A, "2026-10-05", "2026-10-11"), [("12 Lake Road", "CASE-5120")])

    def test_conflicting_sources_are_both_visible(self):
        record_conflict(self.db, S, A, "9 Mill Lane", "2026-10-03", "2026-10-15", "order import")
        values = [v for v, _ in believed(self.db, S, A, "2026-10-20", "2026-10-20")]
        self.assertEqual(sorted(values), ["12 Lake Road", "9 Mill Lane"])

    def test_erasure_deletes_history(self):
        self.assertEqual(erase(self.db, S, "2026-10-27"), 3)
        self.assertEqual(believed(self.db, S, A, "2026-10-05", "2026-10-07"), [])

    def test_fresh_memory_is_empty(self):
        self.assertEqual(believed(open_memory(), S, A, "2026-10-27", "2026-10-27"), [])


if __name__ == "__main__":
    unittest.main()
