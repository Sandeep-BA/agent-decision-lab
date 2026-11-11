"""Tests for get-or-create. Author: Sandeep Belgavi.

The SQLite tests always run (offline, standard library) and cover the non-concurrent behaviour.
The PostgreSQL tests run only when PG_DSN points at a scratch database; they create and drop a
table named tags. Without PG_DSN they are reported as skipped, not passed.
"""
import os
import sqlite3
import unittest
import get_or_create as g


class SqliteAdapter:
    """Lets the same SQL run on sqlite3 by mapping %(n)s to :n."""
    def __init__(self):
        self.c = sqlite3.connect(':memory:', isolation_level=None)
        self.c.execute('CREATE TABLE tags(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)')
        self.c.execute("INSERT INTO tags(name) VALUES ('poetry')")

    def execute(self, sql, params=None):
        return self.c.execute(sql.replace('%(n)s', ':n'), params or {})


class OfflineTest(unittest.TestCase):
    def test_do_nothing_returning_is_empty_for_existing_key(self):
        self.assertEqual(SqliteAdapter().execute(g.DO_NOTHING, {'n': 'poetry'}).fetchall(), [])

    def test_get_or_create_existing_and_new(self):
        db = SqliteAdapter()
        self.assertEqual(g.get_or_create(db, 'poetry'), (1, 'existing'))
        self.assertEqual(g.get_or_create(db, 'travel writing'), (2, 'inserted'))
        self.assertEqual(g.get_or_create(db, 'travel writing'), (2, 'existing'))


@unittest.skipUnless(os.environ.get('PG_DSN'), 'PG_DSN not set: PostgreSQL concurrency tests skipped')
class PostgresConcurrencyTest(unittest.TestCase):
    def setUp(self):
        self.connect = g.pg_connect_factory(os.environ['PG_DSN'])
        admin = self.connect()
        g.reset(admin)
        admin.close()

    def test_do_nothing_returns_no_row_after_waiting(self):
        r = g.concurrent(self.connect, g.DO_NOTHING)
        self.assertTrue(r['blocked'])
        self.assertEqual(r['value'], [])

    def test_cte_union_returns_no_row_under_concurrency(self):
        self.assertEqual(g.concurrent(self.connect, g.CTE_UNION)['value'], [])

    def test_do_update_returns_the_concurrent_row(self):
        self.assertEqual(len(g.concurrent(self.connect, g.DO_UPDATE)['value']), 1)

    def test_get_or_create_returns_the_concurrent_row(self):
        value = g.concurrent(self.connect, g.get_or_create)['value']
        self.assertEqual(value[1], 'existing')


if __name__ == '__main__':
    unittest.main()
