"""Tests for upsert_permission_model. Author: Sandeep Belgavi."""
import io, json, unittest
from contextlib import redirect_stdout
from pathlib import Path
import example as ex

ATTACK = {'url': ex.STORED['url'], 'project': 'catalog', 'proxy': 'http://proxy.attacker.test:3128', 'insecure': True}


class UpsertPermission(unittest.TestCase):
    def test_report_matches_recorded_expected_output(self):
        with redirect_stdout(io.StringIO()):
            report = ex.main()
        self.assertEqual(report, json.loads((Path(__file__).parent / 'expected.json').read_text(encoding='utf-8')))

    def test_vulnerable_upsert_replaces_with_create_only(self):
        ok, status, after, _ = ex.decide('vulnerable', 'create', True, dict(ex.STORED), ATTACK, {'create'})
        self.assertEqual((ok, status, after['proxy']), (True, 'Replaced', ATTACK['proxy']))

    def test_patched_upsert_denies_without_update_and_leaves_record(self):
        ok, status, after, _ = ex.decide('patched', 'create', True, dict(ex.STORED), ATTACK, {'create'})
        self.assertEqual((ok, status), (False, 'PermissionDenied'))
        self.assertEqual(after, ex.STORED)

    def test_new_repository_needs_only_create_in_both_versions(self):
        for v in ('vulnerable', 'patched'):
            self.assertEqual(ex.decide(v, 'create', True, None, ATTACK, {'create'})[1], 'Created')

    def test_identical_create_is_a_no_op(self):
        self.assertEqual(ex.decide('patched', 'create', False, dict(ex.STORED), dict(ex.STORED), {'create'})[1], 'Unchanged')

    def test_different_create_without_upsert_is_rejected(self):
        self.assertEqual(ex.decide('vulnerable', 'create', False, dict(ex.STORED), ATTACK, {'create'})[1], 'InvalidArgument')

    def test_replace_clears_omitted_credentials(self):
        after = ex.replace(ATTACK)
        self.assertEqual(ex.cleared_fields(ex.STORED, after), ['password', 'username'])

    def test_direct_update_requires_update(self):
        self.assertEqual(ex.decide('patched', 'update', False, dict(ex.STORED), ATTACK, {'create'})[1], 'PermissionDenied')

    def test_audit_flags_every_replace_path_without_update(self):
        routes = [f['route'] for f in ex.audit(ex.API)]
        self.assertIn('PUT /stores/{id}', routes)
        self.assertIn('POST /imports (merge mode)', routes)
        self.assertNotIn('PUT /price-lists/{id}', routes)
        self.assertNotIn('POST /repositories', routes)


if __name__ == '__main__':
    unittest.main()
