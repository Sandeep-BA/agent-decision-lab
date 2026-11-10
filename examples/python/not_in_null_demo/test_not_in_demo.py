"""Author: Sandeep Belgavi."""
import unittest
from not_in_demo import run_all


class NotInNull(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run_all()

    def test_not_in_with_a_null_returns_nothing(self):
        self.assertEqual(self.out['not_in'], [])

    def test_null_safe_forms_agree(self):
        expected = ['Geetha', 'Dinky']
        self.assertEqual(self.out['not_in_filtered'], expected)
        self.assertEqual(self.out['not_exists'], expected)
        self.assertEqual(self.out['anti_join'], expected)

    def test_three_valued_predicate(self):
        # 1 NOT IN (2, NULL) is unknown (NULL), 2 NOT IN (2, NULL) is false, 1 NOT IN (2, 3) is true.
        self.assertEqual(self.out['predicate_value'], [(None, 0, 1)])


if __name__ == '__main__':
    unittest.main()
