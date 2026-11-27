"""Tests for mount_flag_race_model. Author: Sandeep Belgavi."""
import io, json, unittest
from contextlib import redirect_stdout
from pathlib import Path
import example as ex


class MountFlagRace(unittest.TestCase):
    def test_report_matches_recorded_expected_output(self):
        with redirect_stdout(io.StringIO()):
            report = ex.main()
        self.assertEqual(report, json.loads((Path(__file__).parent / 'expected.json').read_text(encoding='utf-8')))

    def test_without_a_swap_both_orders_end_read_only(self):
        for order in ('before-fix', 'after-fix'):
            self.assertFalse(ex.run(order, -1)['ro_source_writable'])

    def test_swap_between_readlink_and_remount_redirects_the_flag(self):
        r = ex.run('before-fix', 2)
        self.assertTrue(r['ro_source_writable'])
        self.assertTrue(r['decoy_made_readonly'])
        self.assertIn('host:/srv/decoy', r['trace'][-1])

    def test_readlink_follows_renames_that_happen_before_it(self):
        r = ex.run('before-fix', 1)
        self.assertIn('/vol/a/ro', r['trace'][3])
        self.assertFalse(r['ro_source_writable'])

    def test_staged_order_is_safe_at_every_interleaving(self):
        self.assertFalse(any(ex.run('after-fix', k)['ro_source_writable'] for k in range(-1, 4)))

    def test_path_resolution_crosses_mounts(self):
        fs, _ = ex.container_setup()
        a, b = fs.resolve('/vol/a/ro'), fs.resolve('/vol/b/ro')
        fs.rename_swap('/vol', 'a', 'b')
        self.assertEqual(fs.resolve('/vol/a/ro'), b)
        self.assertEqual(fs.path_of(a), '/vol/b/ro')


if __name__ == '__main__':
    unittest.main()
