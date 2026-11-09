"""Author: Sandeep Belgavi."""
import unittest
from paired_gate import degradation_pvalue


class Gate(unittest.TestCase):
    def test_known_tails(self):
        self.assertAlmostEqual(degradation_pvalue(15, 5), 21700 / 1048576)
        self.assertEqual(degradation_pvalue(5, 0), 0.03125)

    def test_no_evidence_cases(self):
        self.assertEqual(degradation_pvalue(0, 0), 1)
        self.assertEqual(degradation_pvalue(0, 5), 1)

    def test_invalid_counts(self):
        with self.assertRaises(ValueError):
            degradation_pvalue(-1, 2)
        with self.assertRaises(TypeError):
            degradation_pvalue(1.0, 2)


if __name__ == '__main__':
    unittest.main()
