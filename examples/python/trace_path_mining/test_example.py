"""Tests for trace_path_mining. Author: Sandeep Belgavi."""
import io, json, unittest
from contextlib import redirect_stdout
from pathlib import Path
import example as ex


class TracePathMining(unittest.TestCase):
    def setUp(self):
        self.runs = ex.synth_runs()
        self.raw, self.norm, self.compiled, self.rows = ex.mine(self.runs)

    def test_report_matches_recorded_expected_output(self):
        with redirect_stdout(io.StringIO()):
            report = ex.main()
        expected = json.loads((Path(__file__).parent / 'expected.json').read_text(encoding='utf-8'))
        self.assertEqual(report, expected)

    def test_retries_collapse_into_one_variant(self):
        self.assertEqual(ex.normalize(['get_order', 'get_order', 'get_refund']), ('get_order', 'get_refund'))
        self.assertLess(len(self.norm), len(self.raw))

    def test_each_kind_uses_the_smallest_deciding_attribute_set(self):
        decided = {r['kind']: r.get('decided_by') for r in self.rows}
        self.assertEqual(decided['refund_status'], [])
        self.assertEqual(decided['return'], ['within_30_days'])
        self.assertEqual(decided['damaged'], ['over_2000'])
        self.assertIsNone(decided['other'])

    def test_free_form_cases_stay_with_the_agent(self):
        other = [r for r in self.runs if r['kind'] == 'other']
        self.assertTrue(other)
        self.assertTrue(all(ex.route(r, self.compiled) is None for r in other))

    def test_large_damage_claims_keep_the_approval_step(self):
        run = {'kind': 'damaged', 'days_since_delivery': 3, 'order_total': 3200, 'tools': []}
        self.assertIn('request_approval', ex.route(run, self.compiled))

    def test_mismatches_are_the_runs_that_did_something_extra(self):
        extra = [r for r in self.runs if ex.route(r, self.compiled) and ex.normalize(r['tools']) != ex.route(r, self.compiled)]
        self.assertTrue(extra)
        self.assertTrue(all(r['tools'][-1] == 'search_help_articles' for r in extra))

    def test_purity_threshold_rejects_mixed_groups(self):
        mixed = [{'kind': 'x', 'days_since_delivery': 1, 'order_total': 1, 'tools': [t]} for t in 'abcabcabca']
        _, _, compiled, rows = ex.mine(mixed, min_share=0.0)
        self.assertEqual(compiled, {})
        self.assertIsNone(rows[0]['decided_by'])


if __name__ == '__main__':
    unittest.main()
