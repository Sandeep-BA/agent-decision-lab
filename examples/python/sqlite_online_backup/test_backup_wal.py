# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import tempfile
import unittest
from backup_wal import run


class BackupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as d:
            cls.r = run(d)

    def test_source_has_150_committed_orders_with_a_wal(self):
        self.assertEqual(self.r['source']['rows'], 150)
        self.assertGreater(self.r['wal_bytes'], 0)

    def test_main_file_copy_silently_loses_wal_commits(self):
        c = self.r['copy_main_file']
        self.assertEqual((c['integrity'], c['rows']), ('ok', 100))
        self.assertNotEqual(c['sha'], self.r['source']['sha'])

    def test_backup_api_and_vacuum_into_match_the_source(self):
        for key in ('backup_api', 'vacuum_into'):
            self.assertEqual(self.r[key]['rows'], 150, key)
            self.assertEqual(self.r[key]['sha'], self.r['source']['sha'], key)
            self.assertEqual(self.r[key]['integrity'], 'ok', key)

    def test_backup_with_concurrent_commits_ends_consistent_and_current(self):
        b = self.r['backup_during_writes']
        self.assertEqual(b['rows'], 153)
        self.assertEqual(b['sha'], self.r['source_after_writes']['sha'])
        self.assertGreater(b['progress_calls'], 1)


if __name__ == '__main__':
    unittest.main()
