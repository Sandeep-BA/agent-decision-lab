"""Author: Sandeep Belgavi. Tests for structural truncation of tool results."""
import json
import unittest
from example import _size, cap_items, cap_text, demo, fixture, naive_cut


class ToolResultTruncation(unittest.TestCase):
    def test_every_page_fits_and_is_valid_json(self):
        items, offset, seen = fixture(), 0, []
        while offset is not None and offset < len(items):
            page = cap_items(items, 900, offset)
            self.assertLessEqual(_size(page), 900)
            json.loads(json.dumps(page))
            seen.extend(page["items"])
            offset = page["truncation"]["next_offset"]
        self.assertEqual(seen, items)  # pages reassemble exactly, no gaps or duplicates

    def test_last_page_is_not_marked_truncated(self):
        items = fixture()
        page = cap_items(items, 100_000)
        self.assertFalse(page["truncation"]["truncated"])
        self.assertEqual(page["truncation"]["returned"], len(items))

    def test_oversized_single_item_is_reported(self):
        page = cap_items([{"blob": "x" * 500}], 200)
        self.assertEqual(page["items"], [])
        self.assertEqual(page["truncation"]["reason"], "single item exceeds budget")
        self.assertEqual(page["truncation"]["next_offset"], 0)

    def test_tiny_budget_and_bad_offset_raise(self):
        with self.assertRaises(ValueError):
            cap_items(fixture(), 10)
        with self.assertRaises(ValueError):
            cap_items(fixture(), 900, 41)

    def test_text_cut_at_line_and_utf8_boundary(self):
        r = cap_text("line one\nline two\nlíne three\n", 20)
        self.assertEqual(r["text"], "line one\nline two\n")
        r = cap_text("é" * 10, 5)  # 2-byte characters, budget 5 -> 2 whole characters
        self.assertEqual(r["text"], "éé")
        self.assertTrue(r["truncation"]["truncated"])

    def test_naive_slice_breaks_json(self):
        with self.assertRaises(json.JSONDecodeError):
            json.loads(naive_cut(fixture(), 900))
        self.assertFalse(demo()["naive_slice_is_valid_json"])


if __name__ == "__main__":
    unittest.main()
