"""Tests for the run-epoch fencing example. Author: Sandeep Belgavi."""
import unittest
from fencing import LeaseTable, ToolServer, StaleEpoch, scenario


class FencingTest(unittest.TestCase):
    def test_default_timeline(self):
        r = scenario()
        self.assertEqual((r['expiry'], r['wake']), (50, 85))
        self.assertEqual(r['log'][0], 't=55: B acquires R-17 with epoch 2')

    def test_no_fencing_issues_two_refunds(self):
        self.assertEqual(len(scenario()['refunds']), 2)

    def test_fence_on_write_rejects_late_zombie(self):
        r = scenario(fencing=True)
        self.assertEqual([w for _, w, _ in r['refunds']], ['B'])
        self.assertIn('t=85: A epoch 1 -> rejected (epoch 1 < 2)', r['log'])

    def test_fence_on_write_misses_zombie_that_writes_first(self):
        r = scenario(fencing=True, resume_work=40)
        self.assertEqual([w for _, w, _ in r['refunds']], ['A', 'B'])

    def test_register_on_grant_closes_the_window(self):
        r = scenario(fencing=True, register_on_grant=True, resume_work=40)
        self.assertEqual([w for _, w, _ in r['refunds']], ['B'])

    def test_idempotency_hides_duplicate_but_not_stale_status(self):
        r = scenario(idempotent=True)
        self.assertEqual(len(r['refunds']), 1)
        self.assertEqual(r['status']['CASE-4107'], 'refunded by A (epoch 1)')

    def test_short_pause_means_no_takeover(self):
        r = scenario(pause=20)
        self.assertEqual(len(r['refunds']), 1)
        self.assertFalse(any('acquires' in line for line in r['log']))

    def test_lease_table_rules(self):
        t = LeaseTable(ttl=30)
        self.assertEqual(t.acquire('R', 'A', 0), 1)
        self.assertIsNone(t.acquire('R', 'B', 10))
        self.assertFalse(t.renew('R', 'A', 1, 30))
        self.assertEqual(t.acquire('R', 'B', 31), 2)

    def test_server_rejects_older_epoch(self):
        s = ToolServer(fencing=True)
        s.register('R', 3)
        with self.assertRaises(StaleEpoch):
            s.refund('R', 2, 'CASE-1', 'A')


if __name__ == '__main__':
    unittest.main()
