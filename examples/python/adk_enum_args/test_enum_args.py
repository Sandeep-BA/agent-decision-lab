# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

import importlib.util
import unittest

import enum_args as e


class ParseTest(unittest.TestCase):
    def test_accepts_member_and_string(self):
        self.assertIs(e.parse_reason("damaged"), e.Reason.DAMAGED)
        self.assertIs(e.parse_reason(e.Reason.LATE), e.Reason.LATE)

    def test_rejects_unknown_values(self):
        with self.assertRaises(ValueError):
            e.parse_reason("not-a-reason")

    def test_plain_enum_member_does_not_equal_its_string(self):
        self.assertFalse(e.Reason.DAMAGED == "damaged")
        self.assertTrue(e.Channel.WEB == "web")


@unittest.skipUnless(importlib.util.find_spec("google.adk"), "google-adk not installed")
class AdkTest(unittest.TestCase):
    def test_framework_passes_a_member_on_214(self):
        import asyncio, google.adk
        result = asyncio.run(e.run_probe())
        if google.adk.__version__.startswith("2.14"):
            self.assertEqual(result["reason_type"], "Reason")
            self.assertFalse(result["reason_eq"])


if __name__ == "__main__":
    unittest.main()
