"""Tests for the bounded JSON formatting companion; numbers match the article's table. Author: Sandeep Belgavi."""
import json
import unittest

import bounded as b


class Growth(unittest.TestCase):
    def test_growth_equals_nesting_depth(self):
        self.assertEqual(b.growth(b.nested(500)), {'raw_bytes': 1000, 'indented_bytes': 500000, 'compact_bytes': 1000, 'growth': 500})
        self.assertEqual(b.growth(b.nested(900))['indented_bytes'], 1620000)

    def test_two_hundred_kilobytes_become_eighty_megabytes(self):
        g = b.growth(b.nested(400, 100_000))
        self.assertEqual((g['raw_bytes'], g['indented_bytes'], g['compact_bytes'], g['growth']), (200799, 80620798, 300798, 401))


class Bounded(unittest.TestCase):
    def test_small_document_is_formatted(self):
        out = b.bounded_pretty(json.dumps({'case': 'CASE-1042', 'ok': True}).encode())
        self.assertTrue(out.startswith('{\n  "case"'))

    def test_deep_document_is_refused_before_formatting(self):
        with self.assertRaises(ValueError):
            b.bounded_pretty(b.nested(400, 1000).encode())

    def test_brackets_inside_strings_do_not_count(self):
        self.assertEqual(b.max_depth(json.dumps({'title': '[[[[[[ a "quoted" [[[ bracket ]]]'})), 1)

    def test_escaped_quote_does_not_end_the_string(self):
        text = '{"t": "a \\" [[[[ still inside"}'
        self.assertEqual(b.max_depth(text), 1)

    def test_size_limit_applies_first(self):
        with self.assertRaises(ValueError):
            b.bounded_pretty(b'[' + b'0,' * 200_000 + b'0]', max_bytes=1000)


if __name__ == '__main__':
    unittest.main()
