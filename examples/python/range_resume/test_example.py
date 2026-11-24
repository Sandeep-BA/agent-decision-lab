# Author: Sandeep Belgavi. Original behavioral boundary tests.
import unittest,json
from example import *

class Behavior(unittest.TestCase):
    def test_exact_append(self):self.assertEqual(consume(b"ABCD",'"v1"',206,b"EFGH",'"v1"',(4,7,8))["bytes"],b"ABCDEFGH")
    def test_full_response_replaces(self):self.assertEqual(consume(b"ABCD",'"v1"',200,b"12345678",'"v2"')["bytes"],b"12345678")
    def test_wrong_identity(self):
        for saved,received in [('W/"v1"','W/"v1"'),('"v1"','"v2"')]:
            with self.assertRaises(ValueError):consume(b"ABCD",saved,206,b"EFGH",received,(4,7,8))
    def test_wrong_bounds_and_truncation(self):
        for body,bounds in [(b"FGH",(5,7,8)),(b"EFG",(4,7,8)),(b"EFGH",(4,7,9))]:
            with self.assertRaises(ValueError):consume(b"ABCD",'"v1"',206,body,'"v1"',bounds)
    def test_416_is_not_completion(self):
        with self.assertRaises(ValueError):consume(b"ABCD",'"v1"',416,b"",'"v1"')

if __name__ == "__main__":unittest.main()
