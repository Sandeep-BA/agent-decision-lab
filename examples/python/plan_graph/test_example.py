# Author: Sandeep Belgavi. Original behavioral boundary tests.
import unittest,json
from example import *

class Behavior(unittest.TestCase):
    def plan(self): return [{"id":"a","op":"read_fixture","after":[]},{"id":"b","op":"checksum","after":["a"]}]
    def test_success_precedence(self): self.assertEqual(compile_plan(self.plan()),("a","b"))
    def test_missing_dependency_dispatches_nothing(self):
        plan=self.plan();plan[1]["after"]=["ghost"];calls=[]
        with self.assertRaises(ValueError):
            for task in compile_plan(plan): calls.append(task)
        self.assertEqual(calls,[])
    def test_disconnected_cycle_blocks_everything(self):
        plan=self.plan()+[{"id":"x","op":"checksum","after":["y"]},{"id":"y","op":"checksum","after":["x"]}]
        with self.assertRaisesRegex(ValueError,"cyclic"):compile_plan(plan)
    def test_duplicate_not_overwritten(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):compile_plan(self.plan()+[self.plan()[0]])
    def test_unknown_operation_is_rejected(self):
        p=self.plan();p[1]["op"]=[]
        with self.assertRaises(ValueError):compile_plan(p)
    def test_empty_and_oversize(self):
        for p in ([],[{"id":str(i),"op":"compare","after":[]} for i in range(33)]):
            with self.assertRaises(ValueError):compile_plan(p)

if __name__ == "__main__":unittest.main()
