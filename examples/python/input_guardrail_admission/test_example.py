"""Author: Sandeep Belgavi. Admission and remaining-effect invariants."""
import unittest
from example import simulate
class Tests(unittest.TestCase):
 def test_queued_stop(self):self.assertEqual(simulate()['admitted'],[['A',0]])
 def test_earlier_effect_remains(self):self.assertEqual(simulate()['effects'],['A'])
 def test_reject_before_effect(self):self.assertEqual(simulate(reject_at=1)['effects'],[])
 def test_noncooperative(self):self.assertEqual(simulate(reject_at=1,cooperative=False)['effects'],['A'])
 def test_before_start(self):self.assertEqual(simulate(reject_at=0)['admitted'],[])
 def test_blocking(self):self.assertEqual(simulate(blocking=True)['admitted'],[])
 def test_slot_boundary(self):self.assertEqual(simulate(reject_at=4)['admitted'],[['A',0]])
 def test_unchecked_bug(self):self.assertTrue(any(t>=3 for _,t in simulate(guard=False)['admitted']))
 def test_passing_within_window(self):self.assertEqual(len(simulate(reject_at=99)['admitted']),3)
if __name__=='__main__':unittest.main()
