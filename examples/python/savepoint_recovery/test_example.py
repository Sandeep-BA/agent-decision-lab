# Author: Sandeep Belgavi. Original behavioral boundary tests.
import unittest,json
from example import *

class Behavior(unittest.TestCase):
    def test_release_does_not_commit(self):
        t=Transaction();t.save("x");t.insert(1,"a");t.release("x");self.assertEqual(t.durable,{});t.rollback();self.assertEqual(t.working,{})
    def test_rollback_preserves_earlier_work(self):
        t=Transaction();t.insert(1,"a");t.save("x");t.insert(2,"b");t.rollback_to("x");self.assertEqual(t.working,{1:"a"})
    def test_failed_state_requires_recovery(self):
        t=Transaction();t.insert(1,"a");t.save("x")
        with self.assertRaises(ValueError):t.insert(1,"duplicate")
        with self.assertRaises(RuntimeError):t.insert(2,"b")
        t.rollback_to("x");t.insert(2,"b");t.commit();self.assertEqual(t.durable,{1:"a",2:"b"})
    def test_nested_markers_removed(self):
        t=Transaction();t.save("a");t.insert(1,"x");t.save("b");t.rollback_to("a");self.assertEqual([m[0] for m in t.markers],["a"])
        with self.assertRaises(ValueError):t.rollback_to("b")
    def test_full_rollback_discards_every_insert(self):
        t=Transaction();t.insert(1,"a");t.save("x");t.insert(2,"b");t.release("x");t.rollback();self.assertEqual(t.working,{});self.assertEqual(t.durable,{})

if __name__ == "__main__":unittest.main()
