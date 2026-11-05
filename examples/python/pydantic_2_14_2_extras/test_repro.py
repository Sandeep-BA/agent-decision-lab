"""Version-aware tests: each pinned environment asserts the behaviour documented for its pydantic version.
Author: Sandeep Belgavi."""
import json
import pathlib
import unittest

import pydantic

from repro import reproduce

HERE = pathlib.Path(__file__).resolve().parent
V = tuple(int(x) for x in pydantic.VERSION.split('.')[:3])


class Advisories(unittest.TestCase):
    def setUp(self):
        self.r = reproduce()

    def test_qpmf_json_key_check(self):
        if (2, 13, 0) <= V < (2, 14, 2):
            self.assertIn("'refund_override': 1", self.r['qpmf_json'])
        else:
            self.assertEqual(self.r['qpmf_json'], 'ValidationError: string_pattern_mismatch')
        self.assertEqual(self.r['qpmf_python'], 'ValidationError: string_pattern_mismatch')

    def test_3r8g_alias_override(self):
        bad = V < (2, 14, 2)
        self.assertEqual(self.r['3r8g_typeddict'], "accepted: {'amount': %d}" % (999999 if bad else 1200))
        self.assertEqual(self.r['3r8g_dataclass'], 'accepted: %d' % (999999 if bad else 1200))
        self.assertEqual(self.r['3r8g_basemodel'], 'accepted: 1200')  # BaseModel keeps extras separately

    def test_json_key_matching_change(self):
        self.assertEqual(self.r['page_forbid_python'], 'ValidationError: extra_forbidden')
        if V < (2, 14, 2):
            self.assertEqual(self.r['page_forbid_json'], 'accepted: Page(page_size=10)')
            self.assertEqual(self.r['page_allow_json_extras'], 'accepted: {}')
        else:
            self.assertEqual(self.r['page_forbid_json'], 'ValidationError: extra_forbidden')
            self.assertEqual(self.r['page_allow_json_extras'], "accepted: {'page_size': 50}")

    def test_matches_recorded_output_when_pinned(self):
        f = HERE / ('expected_%s.json' % pydantic.VERSION)
        if not f.exists():
            self.skipTest('no recorded output for pydantic ' + pydantic.VERSION)
        self.assertEqual(self.r, json.loads(f.read_text(encoding='utf-8')))


if __name__ == '__main__':
    unittest.main()
