"""Author: Sandeep Belgavi."""
from fractions import Fraction
import unittest
from rebaseline import cohen_kappa, compare, fixture


class Rebaseline(unittest.TestCase):
    def test_kappa_hand_example(self):
        # po = 3/4, pe = 1/2 * 1/4 + 1/2 * 3/4 = 1/2, kappa = (3/4 - 1/2) / (1/2) = 1/2
        self.assertEqual(cohen_kappa([1, 1, 0, 0], [1, 0, 0, 0]), Fraction(1, 2))
        self.assertEqual(cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]), 1)
        self.assertIsNone(cohen_kappa([1, 1, 1], [1, 1, 1]))

    def test_lenient_new_judge_is_rejected(self):
        human, old, new = fixture()
        result = compare(human, old, new)
        self.assertEqual(result['kappa_old_vs_human'], Fraction(5, 8))
        self.assertEqual(result['kappa_new_vs_human'], Fraction(7, 17))
        self.assertEqual((result['flips_to_pass'], result['flips_to_fail']), (3, 0))
        self.assertTrue(result['decision'].startswith('reject'))

    def test_better_judge_still_needs_a_rebaseline(self):
        human, old, _ = fixture()
        result = compare(human, old, list(human))
        self.assertEqual(result['kappa_new_vs_human'], 1)
        self.assertEqual(result['flip_rate'], Fraction(3, 20))
        self.assertTrue(result['decision'].startswith('adopt only with a re-baseline'))

    def test_identical_judge_is_comparable(self):
        human, old, _ = fixture()
        self.assertTrue(compare(human, old, list(old))['decision'].startswith('adopt:'))

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            compare([1, 0], [1], [1, 0])
        with self.assertRaises(ValueError):
            cohen_kappa([1, 2], [1, 0])


if __name__ == '__main__':
    unittest.main()
