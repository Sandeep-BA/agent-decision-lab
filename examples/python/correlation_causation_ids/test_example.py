"""Author: Sandeep Belgavi. Message identity and graph boundary tests."""
import unittest
from example import *
class Tests(unittest.TestCase):
 def test_chain(self):self.assertEqual(ancestry(fixture(),'M4'),['M1','M2','M3','M4'])
 def test_correlated_child(self):
  s=fixture();self.assertTrue(validate_child(s['M1'],s['M2']))
 def test_dropped_lineage(self):
  s=fixture();s['M2']['correlation']='C2';self.assertFalse(validate_child(s['M1'],s['M2']))
 def test_missing_parent(self):
  s=fixture();del s['M2'];self.assertRaises(ValueError,ancestry,s,'M4')
 def test_join(self):
  s=fixture();s['J']={'id':'J','correlation':'C1','causes':['M2','M3'],'kind':'joined'};self.assertEqual(ancestry(s,'J'),['J','M1','M2','M3'])
 def test_malformed_cycle_terminates(self):
  s=fixture();s['M1']['causes']=['M4'];self.assertEqual(len(ancestry(s,'M4')),4)
if __name__=='__main__':unittest.main()
