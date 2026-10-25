"""Author: Sandeep Belgavi. Expected-outcome tests for offset versus keyset paging."""
import json
import os
import unittest

import paging

HERE = os.path.dirname(os.path.abspath(__file__))


class ScanTests(unittest.TestCase):
    def test_offset_duplicates_under_inserts(self):
        r = paging.scan('offset')
        self.assertEqual((r['pages'], r['returned'], r['duplicates'], r['missed']), (21, 1014, 14, 0))

    def test_offset_misses_under_closes(self):
        r = paging.scan('offset', inserts_per_min=1, deletes_per_min=4)
        self.assertEqual((r['duplicates'], r['missed']), (0, 19))

    def test_keyset_is_exact_under_both_write_patterns(self):
        for ins, dels in ((3, 1), (1, 4), (10, 10)):
            r = paging.scan('keyset', inserts_per_min=ins, deletes_per_min=dels)
            self.assertEqual((r['duplicates'], r['missed']), (0, 0), (ins, dels))

    def test_fast_reader_has_fewer_errors(self):
        self.assertLess(paging.scan('offset', think_sec=2)['duplicates'], paging.scan('offset')['duplicates'])

    def test_page_budget_stops_scan(self):
        r = paging.scan('keyset', max_pages=5)
        self.assertEqual(r['pages'], 5)
        self.assertGreater(r['missed'], 0)


class ToolTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(HERE, 'fixtures', 'tickets.json'), encoding='utf-8') as f:
            self.rows = json.load(f)

    def test_keyset_walk_returns_every_row_once_with_ties(self):
        seen, cursor = [], None
        while True:
            page = paging.list_open_tickets(self.rows, cursor, page_size=2)
            seen += [r['id'] for r in page['items']]
            cursor = page['next_cursor']
            if cursor is None:
                break
        self.assertEqual(sorted(seen), [101, 102, 103, 104, 105])
        self.assertEqual(len(seen), len(set(seen)))

    def test_tampered_cursor_is_rejected(self):
        cursor = paging.list_open_tickets(self.rows, page_size=2)['next_cursor']
        raw = bytearray(paging.base64.urlsafe_b64decode(cursor.encode()))
        raw[-3] ^= 1                         # flip a bit in the position
        forged = paging.base64.urlsafe_b64encode(bytes(raw)).decode()
        with self.assertRaises(ValueError):
            paging.list_open_tickets(self.rows, forged)

    def test_page_size_is_capped(self):
        rows = [{'id': i, 'created_at': '2026-10-20T00:00:%02dZ' % (i % 60)} for i in range(500)]
        self.assertEqual(len(paging.list_open_tickets(rows, page_size=10_000)['items']), 100)


if __name__ == '__main__':
    unittest.main()
