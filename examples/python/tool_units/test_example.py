# Author: Sandeep Belgavi. Original behavioral boundary tests.
import unittest,json
from example import *

class Behavior(unittest.TestCase):
    def test_mixed_units(self): self.assertEqual(add(quantity("250","ms"),quantity("1.5","s")).magnitude,Decimal("1.750"))
    def test_equivalent_units(self): self.assertEqual(quantity("1000","ms"),quantity("1","s"))
    def test_dimension_mismatch(self):
        with self.assertRaises(ValueError):add(quantity("1","s"),quantity("1","B"))
    def test_binary_scale_and_zero(self):
        self.assertEqual(quantity("2","KiB").magnitude,Decimal(2048));self.assertEqual(quantity("0","ms").magnitude,0)
    def test_invalid_quantities(self):
        for value in ("NaN","Infinity","-1","not-a-number",1):
            with self.subTest(value=value),self.assertRaises(ValueError):quantity(value,"s")
    def test_unknown_unit_refused(self):
        for unit in ("m","MS",[]):
            with self.assertRaises(ValueError):quantity("1",unit)

if __name__ == "__main__":unittest.main()
