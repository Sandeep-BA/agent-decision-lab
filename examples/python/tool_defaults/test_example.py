# Author: Sandeep Belgavi. Original behavioral boundary tests.
import unittest,json
from example import *

class Behavior(unittest.TestCase):
    def test_omitted_and_false(self): self.assertEqual(normalize({"detail":False})["arguments"],{"limit":20,"detail":False})
    def test_null_zero_string_boolean_limit(self):
        for value in (None,0,"20",True,101):
            with self.subTest(value=value),self.assertRaises(ValueError):normalize({"limit":value})
    def test_unknown_field(self):
        with self.assertRaises(ValueError):normalize({"limt":10})
    def test_version_pins_meaning(self):
        self.assertEqual(normalize({},1)["arguments"]["limit"],20);self.assertEqual(normalize({},2)["arguments"]["limit"],40)
    def test_no_mutation_even_on_failure(self):
        p={"detail":False};normalize(p);self.assertEqual(p,{"detail":False})
        p={"limit":None}
        with self.assertRaises(ValueError):normalize(p)
        self.assertEqual(p,{"limit":None})
    def test_effective_review_payload_is_adapter_payload(self):
        receipt=normalize({"limit":7});reviewed=json.dumps(receipt,sort_keys=True);adapter=[];adapter.append(json.loads(reviewed)["arguments"])
        self.assertEqual(adapter,[{"limit":7,"detail":False}])

if __name__ == "__main__":unittest.main()
