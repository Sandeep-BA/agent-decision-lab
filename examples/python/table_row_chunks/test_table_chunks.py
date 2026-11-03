"""Author: Sandeep Belgavi. Reproduces the table in the article from the synthetic corpus."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import table_chunks as t  # noqa: E402


class TableChunksTest(unittest.TestCase):
    def test_reported_numbers(self):
        self.assertEqual(t.evaluate('fixed'), {'chunks': 12, 'row_and_cell@3': 10, 'answerable@1': 1, 'answerable@3': 1})
        self.assertEqual(t.evaluate('row'), {'chunks': 16, 'row_and_cell@3': 10, 'answerable@1': 0, 'answerable@3': 0})
        self.assertEqual(t.evaluate('row_with_header'), {'chunks': 16, 'row_and_cell@3': 10, 'answerable@1': 7, 'answerable@3': 10})

    def test_serializer_output(self):
        out = t.serialize_rows('Returns policy: return rules by item type',
                               ['Item type', 'Return window', 'Refund method', 'Restocking fee'],
                               [['Signed edition', '7 days', 'Store credit only', '10 percent']])
        self.assertEqual(out, ['Returns policy: return rules by item type. Item type: Signed edition; Return window: 7 days; '
                               'Refund method: Store credit only; Restocking fee: 10 percent.'])

    def test_strict_check_needs_the_header(self):
        self.assertFalse(t.answerable('| Signed edition | 7 days | Store credit only | 10 percent |', 'Signed edition', 'Return window', '7 days'))
        self.assertTrue(t.answerable(t.corpus('row_with_header')[5], 'Signed edition', 'Return window', '7 days'))

    def test_empty_cells_are_skipped(self):
        self.assertEqual(t.serialize_rows('T', ['A', 'B'], [['x', ' ']]), ['T. A: x.'])


if __name__ == '__main__':
    unittest.main()
