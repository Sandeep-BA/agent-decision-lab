# Author: Sandeep Belgavi. Original behavioral boundary tests.
import unittest,json
from example import *

class Behavior(unittest.TestCase):
    def test_policy_only_change_refuses_without_write(self):
        s=Store();old=s.snapshot();s.rows["policy"]=(256,4)
        self.assertEqual(s.apply(old,512),"replan");self.assertEqual(s.rows["task"],(128,7))
    def test_fresh_application_advances_target_revision(self):
        s=Store();self.assertEqual(s.apply(s.snapshot(),256),"applied");self.assertEqual(s.rows["task"],(256,8))
    def test_aba_detected(self):
        s=Store();old=s.snapshot();s.rows["policy"]=(256,4);s.rows["policy"]=(512,5)
        self.assertEqual(s.apply(old,512),"replan")
    def test_incomplete_evidence_refused(self):
        s=Store()
        with self.assertRaises(ValueError):s.apply({"task":s.rows["task"]},256)
    def test_fresh_but_invalid_rule(self):
        s=Store();self.assertEqual(s.apply(s.snapshot(),513),"policy-rejected");self.assertEqual(s.rows["task"],(128,7))
    def test_changed_target_and_bad_type(self):
        s=Store();old=s.snapshot();s.rows["task"]=(256,8);self.assertEqual(s.apply(old,128),"replan")
        with self.assertRaises(ValueError):s.apply(s.snapshot(),True)

if __name__ == "__main__":unittest.main()
