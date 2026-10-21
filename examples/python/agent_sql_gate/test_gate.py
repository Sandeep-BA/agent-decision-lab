"""Tests for the agent SQL gate. Author: Sandeep Belgavi."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

import gate


class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        work = Path(cls.tmp.name)
        cls.app = work / "app.db"
        cls.replica = work / "tenant42.db"
        gate.build_fixture(cls.app)
        cls.replica_rows = gate.build_agent_replica(cls.app, cls.replica, 42)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def strict(self, sql):
        return gate.run(self.replica, sql)

    def test_replica_holds_only_the_tenant(self):
        self.assertEqual(self.replica_rows, 3)

    def test_allowed_aggregate_matches_fixture(self):
        result = self.strict("SELECT count(*), sum(amount_cents) FROM refunds_view")
        self.assertTrue(result.allowed)
        self.assertEqual(result.rows, [(3, 4500)])

    def test_reads_outside_the_allowed_columns_are_refused(self):
        conn = sqlite3.connect(self.replica)
        conn.execute("CREATE TABLE notes (secret TEXT)")
        conn.commit()
        conn.close()
        try:
            result = self.strict("SELECT secret FROM notes")
            self.assertFalse(result.allowed)
            self.assertIn("prohibited", result.reason)
        finally:
            conn = sqlite3.connect(self.replica)
            conn.execute("DROP TABLE notes")
            conn.commit()
            conn.close()

    def test_writes_attach_pragmas_and_extensions_are_refused(self):
        for sql in ("DELETE FROM refunds_view", "ATTACH DATABASE 'x.db' AS x", "PRAGMA writable_schema = 1",
                    "SELECT load_extension('evil')", "CREATE TABLE t (x)"):
            with self.subTest(sql=sql):
                self.assertFalse(self.strict(sql).allowed)

    def test_connection_is_read_only_even_without_the_authorizer(self):
        conn = sqlite3.connect(f"file:{self.replica.as_posix()}?mode=ro", uri=True)
        with self.assertRaises(sqlite3.OperationalError):
            conn.execute("DELETE FROM refunds_view")
        conn.close()

    def test_runaway_statement_is_interrupted(self):
        sql = "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM c WHERE x < 10000000) SELECT count(*) FROM c"
        result = self.strict(sql)
        self.assertFalse(result.allowed)
        self.assertIn("budget", result.reason)

    def test_small_recursive_statement_is_allowed(self):
        sql = "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM c WHERE x < 100) SELECT count(*) FROM c"
        self.assertEqual(self.strict(sql).rows, [(100,)])

    def test_view_source_gate_is_bypassed_by_a_cte_named_like_the_view(self):
        spoof = "WITH refunds_view AS (SELECT * FROM refunds) SELECT sum(amount_cents) FROM refunds_view"
        leaked = gate.run(self.app, spoof, gate.view_source_authorizer)
        self.assertTrue(leaked.allowed)
        self.assertEqual(leaked.rows, [(14400,)])  # both tenants: 4,500 + 9,900
        self.assertFalse(self.strict(spoof).allowed)

    def test_view_source_gate_still_refuses_the_plain_base_table(self):
        self.assertFalse(gate.run(self.app, "SELECT * FROM refunds", gate.view_source_authorizer).allowed)


if __name__ == "__main__":
    unittest.main()
