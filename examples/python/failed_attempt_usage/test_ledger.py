# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import unittest
from ledger import ATTEMPTS, per_attempt, run


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.r = run()

    def test_success_only_accounting_undercounts(self):
        self.assertEqual(self.r['before'], {'requests': 3, 'tokens': 36, 'unreported_attempts': 0})

    def test_per_attempt_accounting(self):
        self.assertEqual(self.r['after'], {'requests': 3, 'tokens': 64, 'unreported_attempts': 1})

    def test_double_counting_is_detectable(self):
        self.assertEqual(self.r['double_counted']['tokens'], 92)

    def test_exhausted_retries_still_cost_tokens(self):
        self.assertEqual(self.r['retries_exhausted'], {'before': 0, 'after': 58})

    def test_budget_decision_flips(self):
        self.assertEqual(self.r['budget_60'], {'before': 'continue', 'after': 'stop'})

    def test_replaying_an_attempt_does_not_add_it_twice(self):
        self.assertEqual(per_attempt(ATTEMPTS + [ATTEMPTS[0]])['tokens'], 64)


if __name__ == '__main__':
    unittest.main()
