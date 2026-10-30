"""Tests for cacheinval.py. Author: Sandeep Belgavi."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cacheinval as ci


class CacheInvalidationTest(unittest.TestCase):
    def test_direct_database_write_is_stale_until_the_ttl(self):
        r = ci.scenario_direct_write()
        self.assertEqual(r['t20'], 12)            # storefront still shows 12 copies
        self.assertEqual(r['t299'], 12)
        self.assertEqual(r['t300'], 0)            # the cached copy expired at 0 + TTL

    def test_service_write_is_fresh_immediately(self):
        self.assertEqual(ci.scenario_service_write()['t20'], 0)

    def test_change_stream_is_stale_only_until_the_consumer_runs(self):
        r = ci.scenario_change_stream(lag=2)
        self.assertEqual(r['before_consumer'], 12)
        self.assertEqual(r['after_consumer'], 0)

    def test_plain_delete_lets_a_slow_refill_store_the_old_row(self):
        r = ci.scenario_slow_refill(versioned=False)
        self.assertTrue(r['refill_stored'])
        self.assertEqual(r['t3'], 12)

    def test_versioned_tombstone_refuses_the_slow_refill(self):
        r = ci.scenario_slow_refill(versioned=True)
        self.assertFalse(r['refill_stored'])
        self.assertEqual(r['t3'], 0)

    def test_invalidation_never_removes_a_newer_entry(self):
        db, cache, _ = ci.fresh()
        svc = ci.CatalogService(db, cache)
        svc.set_stock('BK-4001', 5, 0)            # version 2
        svc.read('BK-4001', 1)                    # cache now holds version 2
        self.assertFalse(cache.invalidate('book:BK-4001', 1, 2))   # a late event for version 1
        self.assertEqual(svc.read('BK-4001', 3)['stock'], 5)

    def test_consumer_covers_every_writer(self):
        db, cache, _ = ci.fresh()
        consumer = ci.ChangeStreamConsumer(db, cache, position=len(db.log))
        db.update('BK-4001', 3)
        db.update('BK-4001', 2)
        self.assertEqual(consumer.poll(5), 2)


if __name__ == '__main__':
    unittest.main()
