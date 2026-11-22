# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import math
import unittest
from formula import FormulaError, compile_formula, run


class FormulaTest(unittest.TestCase):
    def setUp(self):
        self.r = run()

    def test_f1_over_running_totals(self):
        self.assertEqual(self.r['f1'], 0.75)
        self.assertEqual(self.r['zero_rows_f1'], 0.0)

    def test_unguarded_division_produces_nan(self):
        self.assertEqual(self.r['unguarded_zero_division'], 'nan')

    def test_each_rejection_happens_at_compile_time(self):
        self.assertEqual(self.r['rejected'], {
            'max(tp, fp)': 'function calls are not allowed: max(...)',
            'tp.constructor': 'property access is not allowed',
            'tp = 1': 'assignments are not allowed',
            '0 < tp < 1': 'use separate comparisons in a conditional instead of a comparison chain',
            'xxxxxxxxxxxxxxxxxxxx': 'formula exceeds 1024 characters',
            'tp ** 2': 'operator ** is not allowed',
            'tp; fp': 'expected a single expression'})

    def test_a_misspelled_score_passes_syntax_and_fails_every_row(self):
        t = self.r['typo_without_name_check']
        self.assertEqual((t['value'], t['debug_lines']), (0.0, 4))
        self.assertIn('unknown scores', self.r['typo_with_name_check'])

    def test_parenthesized_comparison_and_precedence(self):
        fn, names = compile_formula('m', '(a < b) == 1 ? -a + b * 2 : 0')
        self.assertEqual(fn({'a': 1, 'b': 3}), 5.0)
        self.assertEqual(names, {'a', 'b'})
        self.assertEqual(self.r['range_check'], 1.0)

    def test_1024_characters_is_allowed(self):
        f = '1' + ' ' * 1023
        self.assertEqual(compile_formula('m', f)[0]({}), 1.0)
        with self.assertRaises(FormulaError):
            compile_formula('m', f + ' ')

    def test_division_follows_javascript_signs(self):
        fn, _ = compile_formula('m', 'a / b')
        self.assertTrue(math.isinf(fn({'a': -1, 'b': 0})) and fn({'a': -1, 'b': 0}) < 0)


if __name__ == '__main__':
    unittest.main()
