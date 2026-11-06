"""Tests for the tool schema portability companion. Author: Sandeep Belgavi.

The GenaiConversion tests run only when google-genai 3.0.0 is installed (pip install -r requirements.txt);
they pin what that SDK version's conversion did on 2026-11-06, offline, with no API call.
"""
import copy
import json
import logging
import pathlib
import unittest

import portability as pt

HERE = pathlib.Path(__file__).resolve().parent
SCHEMA = json.loads((HERE / 'fixtures' / 'resolve_case.json').read_text(encoding='utf-8'))

try:
    from google import genai
    from google.genai import types
    GENAI = getattr(genai, '__version__', '') == '3.0.0'
except ImportError:
    GENAI = False


class Subsets(unittest.TestCase):
    def test_openai_strict_wants_every_property_required(self):
        self.assertEqual(pt.problems(SCHEMA, 'openai_strict'), ['$: every property must be required (missing note)'])

    def test_claude_strict_refuses_numeric_and_length_limits(self):
        p = pt.problems(SCHEMA, 'claude_strict')
        self.assertEqual(len(p), 5)
        self.assertIn('$.properties.amount: multipleOf', p)

    def test_gemini_sdk_type_refuses_multiple_of(self):
        self.assertEqual(pt.problems(SCHEMA, 'gemini_sdk_schema'), ['$.properties.amount: multipleOf'])

    def test_portable_cores_pass_their_own_check(self):
        for target in pt.UNSUPPORTED:
            core = pt.portable_core(copy.deepcopy(SCHEMA), target)
            self.assertEqual(pt.problems(core, target), [], target)

    def test_limits_move_into_the_description(self):
        core = pt.portable_core(SCHEMA, 'claude_strict')
        self.assertIn('maximum 500', core['properties']['amount']['description'])

    def test_missing_additional_properties_is_reported(self):
        s = {'type': 'object', 'properties': {'a': {'type': 'string'}}, 'required': ['a']}
        self.assertEqual(pt.problems(s, 'claude_strict'), ['$: additionalProperties must be false'])


@unittest.skipUnless(GENAI, 'google-genai 3.0.0 not installed')
class GenaiConversion(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def test_conversion_drops_additional_properties_and_makes_null_nullable(self):
        s = copy.deepcopy(SCHEMA)
        del s['properties']['amount']['multipleOf']
        out = types.Schema.from_json_schema(json_schema=types.JSONSchema(**s), api_option='GEMINI_API')
        d = out.model_dump(mode='json', exclude_none=True)
        self.assertNotIn('additional_properties', d)
        self.assertTrue(d['properties']['note']['nullable'])
        self.assertEqual(d['properties']['case_id']['pattern'], '^CASE-[0-9]{4}$')

    def test_typed_json_schema_rejects_multiple_of(self):
        with self.assertRaises(Exception):
            types.JSONSchema(**SCHEMA)

    def test_parameters_json_schema_is_passed_through(self):
        fd = types.FunctionDeclaration(name='resolve_case', parameters_json_schema=SCHEMA)
        self.assertEqual(fd.parameters_json_schema['properties']['amount']['multipleOf'], 0.01)


if __name__ == '__main__':
    unittest.main()
