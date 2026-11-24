# Author: Sandeep Belgavi. Original behavioral boundary tests.
import unittest,json
from example import *

class Behavior(unittest.TestCase):
    def test_protected_supplied_closure(self):self.assertTrue(audit([Resource("parent","administrator",0o755),Resource("exe","administrator",0o755)])["allowed"])
    def test_writable_parent_refused(self):self.assertEqual(audit([Resource("parent","administrator",0o777),Resource("exe","administrator",0o755)])["reasons"],["shared write access: parent"])
    def test_user_owned_helper_refused(self):self.assertFalse(audit([Resource("wrapper","administrator",0o755),Resource("helper","user",0o755)])["allowed"])
    def test_empty_and_duplicate(self):
        self.assertFalse(audit([])["allowed"]);r=Resource("exe","administrator",0o755);self.assertFalse(audit([r,r])["allowed"])
    def test_omitted_parent_is_an_explicit_limit(self):self.assertTrue(audit([Resource("exe","administrator",0o755)])["allowed"])

if __name__ == "__main__":unittest.main()
