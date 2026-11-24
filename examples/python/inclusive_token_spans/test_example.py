"""Author: Sandeep Belgavi. Schema and aggregation regression tests."""
import unittest
from example import *
class Tests(unittest.TestCase):
 def test_inclusive(self):self.assertEqual(demo()['uncached'],200)
 def test_missing(self):self.assertIsNone(normalize({'total':100})['uncached'])
 def test_no_total(self):self.assertIsNone(normalize({'cache_read':10})['total'])
 def test_negative(self):self.assertRaises(ValueError,normalize,{'total':-1})
 def test_bool(self):self.assertRaises(ValueError,normalize,{'total':True})
 def test_over_total(self):self.assertRaises(ValueError,normalize,{'total':10,'cache_read':9,'cache_create':2})
 def test_zero(self):self.assertIsNone(aggregate([])['cache_share'])
 def test_dedup_and_parent(self):
  r={'span_id':'a','kind':'model_request','total':100,'cache_read':50,'cache_create':0};p=dict(r,span_id='p',kind='parent');self.assertEqual(aggregate([r,r,p])['total'],100)
 def test_weighted_ratio(self):
  rows=[{'span_id':'a','kind':'model_request','total':10,'cache_read':10,'cache_create':0},{'span_id':'b','kind':'model_request','total':1000,'cache_read':0,'cache_create':0}];self.assertAlmostEqual(aggregate(rows)['cache_share'],10/1010)
if __name__=='__main__':unittest.main()
