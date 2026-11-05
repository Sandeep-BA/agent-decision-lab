"""Tests for the patch-semantics companion. Author: Sandeep Belgavi."""
import json
import pathlib
import unittest

from patches import PatchConflict, apply_json_patch, compile_ops, merge_patch, run

HERE = pathlib.Path(__file__).resolve().parent
FIXTURE = json.loads((HERE / 'fixtures' / 'tanishka.json').read_text(encoding='utf-8'))


class MergePatchRules(unittest.TestCase):
    def test_rfc7396_appendix_examples(self):
        # A selection of the test cases in RFC 7396 Appendix A.
        cases = [({"a": "b"}, {"a": "c"}, {"a": "c"}), ({"a": "b"}, {"b": "c"}, {"a": "b", "b": "c"}),
                 ({"a": "b"}, {"a": None}, {}), ({"a": ["b"]}, {"a": "c"}, {"a": "c"}),
                 ({"a": [{"b": "c"}]}, {"a": [1]}, {"a": [1]}), ({"e": None}, {"a": 1}, {"e": None, "a": 1}),
                 ({}, {"a": {"bb": {"ccc": None}}}, {"a": {"bb": {}}}), (["a", "b"], ["c", "d"], ["c", "d"])]
        for target, patch, want in cases:
            self.assertEqual(merge_patch(target, patch), want)

    def test_null_deletes_and_array_replaces(self):
        out = run(FIXTURE)['merge_patch']
        self.assertEqual(out['addresses'], 1)
        self.assertEqual(out['phone'], 'deleted')
        self.assertFalse(out['marketing_opt_in'])  # overwrote the concurrent website change


class TypedTool(unittest.TestCase):
    def test_append_keeps_existing_items_and_untouched_fields(self):
        out = run(FIXTURE)['typed_json_patch']
        self.assertEqual(out['ops'], [{"op": "add", "path": "/addresses/-", "value": {"label": "office", "line1": "14 Mill Road"}}])
        self.assertEqual(out['addresses'], 3)
        self.assertEqual(out['phone'], '+91 90000 11111')
        self.assertTrue(out['marketing_opt_in'])

    def test_stale_set_is_rejected_by_test_operation(self):
        self.assertTrue(run(FIXTURE)['stale_consent_change'].startswith('conflict'))

    def test_failed_test_leaves_document_unchanged(self):
        doc = {"a": {"b": {"c": "foo"}}}
        with self.assertRaises(PatchConflict):
            apply_json_patch(doc, [{"op": "replace", "path": "/a/b/c", "value": 42}, {"op": "test", "path": "/a/b/c", "value": "C"}])
        self.assertEqual(doc, {"a": {"b": {"c": "foo"}}})

    def test_unknown_field_refused(self):
        with self.assertRaises(ValueError):
            compile_ops([("set", "email", "x@example.org")], FIXTURE['record'])

    def test_unknown_field_never_becomes_null(self):
        ops = compile_ops([("append", "addresses", {"label": "office"})], {})
        self.assertNotIn(None, [op.get('value') for op in ops])

    def test_matches_expected_output(self):
        want = json.loads((HERE / 'expected_output.json').read_text(encoding='utf-8'))
        self.assertEqual(run(FIXTURE), want)


if __name__ == '__main__':
    unittest.main()
