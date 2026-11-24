"""Author: Sandeep Belgavi. Boundary, offset and DST fixtures."""
import unittest
from example import *
class Tests(unittest.TestCase):
 def test_india(self):
  a,b=bounds('2026-11-24','Asia/Kolkata');self.assertEqual(a.isoformat(),'2026-11-23T18:30:00+00:00');self.assertEqual(partitions(a,b),['2026-11-23','2026-11-24'])
 def test_half_open(self):
  a,b=bounds('2026-11-24','Asia/Kolkata');self.assertEqual(select([{'id':'start','at':a.isoformat()},{'id':'end','at':b.isoformat()}],a,b),['start'])
 def test_offsets(self):
  a,b=bounds('2026-11-24','Asia/Kolkata');self.assertEqual(select([{'id':'A','at':'2026-11-24T00:00:00+05:30'},{'id':'B','at':'2026-11-23T18:30:00Z'}],a,b),['A','B'])
 def test_dst_short(self):
  a,b=bounds('2026-03-08','America/New_York');self.assertEqual((b-a).total_seconds(),23*3600)
 def test_dst_long(self):
  a,b=bounds('2026-11-01','America/New_York');self.assertEqual((b-a).total_seconds(),25*3600)
 def test_naive_rejected(self):self.assertRaises(ValueError,select,[{'id':'x','at':'2026-11-24T00:00:00'}],*bounds('2026-11-24','UTC'))
 def test_utc_midnight(self):self.assertEqual(partitions(*bounds('2026-11-24','UTC')),['2026-11-24'])
if __name__=='__main__':unittest.main()
