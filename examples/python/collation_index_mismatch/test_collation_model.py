"""Author: Sandeep Belgavi. Expected outcomes for the collation-change model."""
import unittest
from collation_model import SHELF, build_index, search, order_violations, insert_unique, old_key, new_key


class CollationTests(unittest.TestCase):
    def setUp(self):
        self.idx = build_index(SHELF)

    def test_wiki_pair_reorders(self):
        self.assertEqual(sorted(["1-1", "11"], key=old_key), ["1-1", "11"])
        self.assertEqual(sorted(["11", "1-1"], key=new_key), ["1-1", "11"])
        self.assertNotEqual(sorted(["11", "1-2"], key=old_key), sorted(["11", "1-2"], key=new_key))

    def test_same_comparator_finds_everything(self):
        self.assertTrue(all(search(self.idx, v, old_key)[0] for v in SHELF))
        self.assertEqual(order_violations(self.idx, old_key), [])

    def test_changed_comparator_misses_rows(self):
        missed = [v for v in SHELF if not search(self.idx, v)[0]]
        self.assertEqual(missed, ["1-2", "1 3", "A-2"])

    def test_order_check_reports_the_damage(self):
        self.assertEqual(order_violations(self.idx), [("11", "1-2"), ("12", "1 3"), ("A10", "A-2")])

    def test_unique_check_admits_a_duplicate(self):
        copy = list(self.idx)
        self.assertTrue(insert_unique(copy, "1-2"))
        self.assertEqual(copy.count("1-2"), 2)

    def test_rebuild_repairs(self):
        rebuilt = build_index(SHELF, new_key)
        self.assertTrue(all(search(rebuilt, v)[0] for v in SHELF))
        self.assertEqual(order_violations(rebuilt), [])


if __name__ == "__main__":
    unittest.main()
