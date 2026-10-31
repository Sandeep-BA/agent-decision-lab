"""Author: Sandeep Belgavi. Tests for the expand-contract rename example."""
import sqlite3
import unittest
from pathlib import Path

import migration as m

FIXTURES = Path(__file__).resolve().parent / 'fixtures'


def fresh(rows=12):
    conn = sqlite3.connect(':memory:')
    m.create(conn, rows)
    m.expand(conn)
    return conn


class ExpandTests(unittest.TestCase):
    def test_backfill_in_batches_leaves_no_half_filled_rows(self):
        conn = fresh(12)
        self.assertEqual(m.backfill(conn, batch=5), 3)
        self.assertEqual(m.half_filled(conn), 0)

    def test_old_and_new_writers_stay_in_step(self):
        conn = fresh()
        m.backfill(conn)
        m.tool_set_refund_v1(conn, 'CASE-6003', 12.34)
        self.assertEqual(m.tool_get_refund_v2(conn, 'CASE-6003')['refund_amount_minor'], 1234)
        m.tool_set_refund_v2(conn, 'CASE-6004', 999)
        self.assertAlmostEqual(m.tool_get_refund_v1(conn, 'CASE-6004')['refund_amount'], 9.99)

    def test_inserts_through_either_column_fill_both(self):
        conn = fresh(0)
        conn.execute("INSERT INTO returns (case_id, refund_amount) VALUES ('CASE-7001', 4.5)")
        conn.execute("INSERT INTO returns (case_id, refund_amount_minor) VALUES ('CASE-7002', 250)")
        self.assertEqual(m.tool_get_refund_v2(conn, 'CASE-7001')['refund_amount_minor'], 450)
        self.assertAlmostEqual(m.tool_get_refund_v1(conn, 'CASE-7002')['refund_amount'], 2.5)

    def test_only_old_column_writes_are_logged(self):
        conn = fresh()
        m.backfill(conn)
        m.tool_set_refund_v2(conn, 'CASE-6001', 100)
        self.assertEqual(conn.execute('SELECT count(*) FROM migration_old_writes').fetchone()[0], 0)
        m.tool_set_refund_v1(conn, 'CASE-6001', 2.0)
        self.assertEqual(conn.execute('SELECT count(*) FROM migration_old_writes').fetchone()[0], 1)


class ContractTests(unittest.TestCase):
    def test_scanner_finds_the_old_name_outside_code(self):
        hits = m.scan_references(FIXTURES)
        self.assertEqual(set(hits), {'evals/case_6003.json', 'memory/session_notes.jsonl', 'prompts/refund_agent.md', 'tools/get_refund.json'})
        self.assertNotIn('refund_amount_minor', ''.join(hits))

    def test_contract_is_refused_while_writes_or_references_remain(self):
        conn = fresh()
        m.backfill(conn)
        m.tool_set_refund_v1(conn, 'CASE-6002', 1.0)
        ok, reasons = m.contract_allowed(conn, m.scan_references(FIXTURES))
        self.assertFalse(ok)
        self.assertEqual(len(reasons), 2)

    def test_contract_drops_the_old_column(self):
        conn = fresh()
        m.backfill(conn)
        self.assertTrue(m.contract_allowed(conn, {})[0])
        m.contract(conn)
        cols = [r[1] for r in conn.execute('PRAGMA table_info(returns)')]
        self.assertEqual(cols, ['id', 'case_id', 'refund_amount_minor'])
        with self.assertRaises(sqlite3.OperationalError):
            m.tool_get_refund_v1(conn, 'CASE-6001')


if __name__ == '__main__':
    unittest.main()
