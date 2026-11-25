"""Author: Sandeep Belgavi. Tests for the Valkey 9.2 upgrade models."""
import math
import unittest
from example import audit_bounds, first_save, parse_bound, zcount


class ScoreBounds(unittest.TestCase):
    def test_bare_paren_and_empty(self):
        self.assertEqual(parse_bound("(", "9.0"), (0.0, True))
        self.assertEqual(parse_bound("", "9.0"), (0.0, False))
        for b in ("(", ""):
            with self.assertRaises(ValueError):
                parse_bound(b, "9.2")

    def test_valid_bounds_unchanged(self):
        for b, v in (("(5", (5.0, True)), ("-inf", (-math.inf, False)), ("+inf", (math.inf, False)), ("2.5", (2.5, False))):
            self.assertEqual(parse_bound(b, "9.0"), parse_bound(b, "9.2"))
            self.assertEqual(parse_bound(b), v)

    def test_zcount_semantics(self):
        self.assertEqual(zcount([0, 0.5, 1, 2], "(", "+inf", "9.0"), 3)  # silently "(0"
        self.assertEqual(zcount([0, 0.5, 1, 2], "(0", "+inf"), 3)
        with self.assertRaises(ValueError):
            zcount([0], "(", "+inf")

    def test_audit_flags_only_changed_bounds(self):
        self.assertEqual([c["bound"] for c in audit_bounds(["(", "", "(5", "(abc", "1"])], ["(", ""])


class SavePoints(unittest.TestCase):
    RULES = [(3600, 1), (300, 100), (60, 10000)]

    def test_expiry_alone_triggers_from_9_2(self):
        self.assertIsNone(first_save(self.RULES, 0.0, 50, count_expiry=False))
        self.assertEqual(first_save(self.RULES, 0.0, 50, count_expiry=True), 200)

    def test_write_heavy_workload_unaffected(self):
        self.assertEqual(first_save(self.RULES, 500, 0, count_expiry=False), 60)
        self.assertEqual(first_save(self.RULES, 500, 50, count_expiry=True), 60)


if __name__ == "__main__":
    unittest.main()
