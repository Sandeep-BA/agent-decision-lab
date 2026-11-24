# Author: Sandeep Belgavi. Original behavioral boundary tests.
import unittest,json
from example import *

class Behavior(unittest.TestCase):
    def owned(self):return ProcessRecord(42,"a","g")
    def test_reuse_refused(self):self.assertEqual(cleanup_decision(self.owned(),ProcessRecord(42,"b","g"),"g"),"refuse-different-process")
    def test_missing_identity_refused(self):self.assertEqual(cleanup_decision(self.owned(),ProcessRecord(42,None,"g"),"g"),"refuse-unknown-identity")
    def test_generation_requires_reconciliation(self):self.assertEqual(cleanup_decision(self.owned(),self.owned(),"new"),"reconcile-supervisor-generation")
    def test_absence_is_not_identity_failure(self):self.assertEqual(cleanup_decision(self.owned(),None,"g"),"already-gone")
    def test_exact_match_only_is_eligible(self):self.assertEqual(cleanup_decision(self.owned(),self.owned(),"g"),"eligible-for-bound-handle-cleanup")
    def test_other_owner_refused(self):self.assertEqual(cleanup_decision(self.owned(),ProcessRecord(42,"a","other"),"g"),"refuse-unowned-process")

if __name__ == "__main__":unittest.main()
