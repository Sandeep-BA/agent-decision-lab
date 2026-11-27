"""Tests for tool_deprecation_inventory. Author: Sandeep Belgavi."""
import io, json, unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
import example as ex


class ToolDeprecation(unittest.TestCase):
    def test_report_matches_recorded_expected_output(self):
        with redirect_stdout(io.StringIO()):
            report = ex.main()
        self.assertEqual(json.loads(json.dumps(report)), json.loads((Path(__file__).parent / 'expected.json').read_text(encoding='utf-8')))

    def test_deprecation_is_a_structured_date_and_sunset_an_http_date(self):
        h = ex.headers(ex.PLAN)
        self.assertEqual(h['Deprecation'], '@' + str(int(datetime(2026, 12, 1, tzinfo=timezone.utc).timestamp())))
        self.assertTrue(h['Sunset'].endswith('GMT'))
        self.assertIn('rel="deprecation"', h['Link'])

    def test_sunset_before_deprecation_is_rejected(self):
        bad = dict(ex.PLAN, sunset_at=datetime(2026, 11, 1, tzinfo=timezone.utc))
        with self.assertRaises(ValueError):
            ex.headers(bad)

    def test_alias_translates_only_the_known_argument_shape(self):
        ok, why = ex.alias({'args': {'order_ref': 'ORD-9'}})
        self.assertEqual((ok, why), ({'tool': 'lookup_order', 'args': {'order_id': 'ORD-9'}}, 'translated'))
        self.assertIsNone(ex.alias({'args': {'order_ref': 'ORD-9', 'include': 'history'}})[0])

    def test_inventory_separates_prompt_versions_and_services(self):
        now = datetime(2026, 12, 20, 12, tzinfo=timezone.utc)
        keys = {(i['caller'], i['prompt_version']) for i in ex.inventory(ex.synth_log(now), now)}
        self.assertIn(('helpdesk-agent', 'prompt-41'), keys)
        self.assertIn(('helpdesk-agent', 'prompt-42'), keys)
        self.assertIn(('nightly-report (service)', None), keys)

    def test_gate_needs_both_the_date_and_an_empty_inventory(self):
        after = datetime(2027, 2, 1, tzinfo=timezone.utc)
        self.assertFalse(ex.removal_gate([{'calls': 1}], after, ex.PLAN)['may_remove'])
        self.assertTrue(ex.removal_gate([], after, ex.PLAN)['may_remove'])

    def test_listing_marks_deprecation_without_a_protocol_field(self):
        listing = ex.tool_listing(ex.PLAN)
        self.assertTrue(listing['description'].startswith('DEPRECATED'))
        self.assertIn('bookstore.test/deprecation', listing['_meta'])


if __name__ == '__main__':
    unittest.main()
