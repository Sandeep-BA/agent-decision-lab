"""Tests for es_bulk_retry_model. Author: Sandeep Belgavi."""
import io, json, unittest
from contextlib import redirect_stdout
from pathlib import Path
import example as ex


class EsBulkRetry(unittest.TestCase):
    def test_report_matches_recorded_expected_output(self):
        with redirect_stdout(io.StringIO()):
            report = ex.main()
        self.assertEqual(report, json.loads((Path(__file__).parent / 'expected.json').read_text(encoding='utf-8')))

    def test_lost_response_without_ids_duplicates_every_document(self):
        r = ex.export(ex.batch(), ex.V166, ['lost-response'])
        self.assertEqual((r['stored_documents'], r['duplicates'], r['reported_failed']), (10, 5, []))

    def test_deterministic_ids_turn_duplicates_into_409_reports(self):
        r = ex.export(ex.batch(with_ids=True), ex.V166, ['lost-response'])
        self.assertEqual((r['stored_documents'], r['duplicates']), (5, 0))
        self.assertEqual({s for _, s in r['reported_failed']}, {409})

    def test_old_defaults_report_a_timeout_even_though_documents_landed(self):
        r = ex.export(ex.batch(), ex.V165, ['lost-response'])
        self.assertEqual((r['stored_documents'], r['lost_records']), (5, 0))
        self.assertEqual(len(r['reported_failed']), 5)

    def test_503_before_apply_is_recovered_by_the_new_defaults_only(self):
        self.assertEqual(ex.export(ex.batch(), ex.V165, ['http-503-before-apply'])['lost_records'], 5)
        self.assertEqual(ex.export(ex.batch(), ex.V166, ['http-503-before-apply'])['lost_records'], 0)

    def test_document_level_429_retries_only_the_rejected_documents(self):
        r = ex.export(ex.batch(), ex.V166, [('doc-429', {1, 3})])
        self.assertEqual((r['stored_documents'], r['attempts']), (5, 2))
        self.assertIn('[201, 429, 201, 429, 201]', r['trace'][0])
        self.assertEqual(r['trace'][1], 'attempt 2: item statuses [201, 201]')

    def test_a_400_is_retried_to_the_limit_and_still_fails(self):
        r = ex.export(ex.batch(), ex.V166, ['http-400'] * 3)
        self.assertEqual((r['attempts'], r['stored_documents']), (3, 0))

    def test_store_rejects_existing_explicit_ids(self):
        s = ex.Store()
        self.assertEqual(s.create({'_id': 'x', 'body': {}}), 201)
        self.assertEqual(s.create({'_id': 'x', 'body': {}}), 409)


if __name__ == '__main__':
    unittest.main()
