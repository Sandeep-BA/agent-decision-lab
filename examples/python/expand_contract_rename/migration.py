"""Expand-contract rename of returns.refund_amount (pounds) to refund_amount_minor (pence), with agent clients.

Author: Sandeep Belgavi. Companion to "Renaming a Column That Agents Still Use" (aicassindra.com).
SQLite stands in for the production database; its AFTER triggers play the part of the PostgreSQL BEFORE
trigger in the article. Synthetic data for Belgavi's Book Store; no model or network is used.
"""
import re
import sqlite3
from pathlib import Path

OLD, NEW = 'refund_amount', 'refund_amount_minor'


def create(conn, rows=12):
    conn.execute('CREATE TABLE returns (id INTEGER PRIMARY KEY, case_id TEXT, refund_amount NUMERIC)')
    conn.execute('CREATE TABLE migration_old_writes (row_id INTEGER, at TEXT)')
    conn.executemany('INSERT INTO returns (case_id, refund_amount) VALUES (?, ?)',
                     [('CASE-%04d' % (6000 + i), round(3 + i * 1.25, 2)) for i in range(rows)])


def expand(conn):
    conn.execute('ALTER TABLE returns ADD COLUMN refund_amount_minor INTEGER')
    conn.executescript('''
    CREATE TRIGGER returns_sync_insert AFTER INSERT ON returns BEGIN
      UPDATE returns SET refund_amount_minor = CAST(round(NEW.refund_amount * 100) AS INTEGER)
        WHERE id = NEW.id AND NEW.refund_amount_minor IS NULL AND NEW.refund_amount IS NOT NULL;
      UPDATE returns SET refund_amount = NEW.refund_amount_minor / 100.0
        WHERE id = NEW.id AND NEW.refund_amount IS NULL AND NEW.refund_amount_minor IS NOT NULL;
    END;
    CREATE TRIGGER returns_sync_new AFTER UPDATE OF refund_amount_minor ON returns
      WHEN NEW.refund_amount_minor IS NOT OLD.refund_amount_minor BEGIN
      UPDATE returns SET refund_amount = NEW.refund_amount_minor / 100.0 WHERE id = NEW.id;
    END;
    CREATE TRIGGER returns_sync_old AFTER UPDATE OF refund_amount ON returns
      WHEN NEW.refund_amount IS NOT OLD.refund_amount
       AND CAST(round(NEW.refund_amount * 100) AS INTEGER) IS NOT NEW.refund_amount_minor BEGIN
      -- The second condition skips the nested update made by returns_sync_new, which already agrees.
      UPDATE returns SET refund_amount_minor = CAST(round(NEW.refund_amount * 100) AS INTEGER) WHERE id = NEW.id;
      INSERT INTO migration_old_writes VALUES (NEW.id, datetime('now'));
    END;''')


def backfill(conn, batch=5):
    """Fill old rows in batches; returns the number of batches that changed rows."""
    batches = 0
    while True:
        cur = conn.execute('''UPDATE returns SET refund_amount_minor = CAST(round(refund_amount * 100) AS INTEGER)
            WHERE id IN (SELECT id FROM returns WHERE refund_amount_minor IS NULL AND refund_amount IS NOT NULL
                         ORDER BY id LIMIT ?)''', (batch,))
        if cur.rowcount == 0:
            return batches
        batches += 1


def half_filled(conn):
    return conn.execute('SELECT count(*) FROM returns WHERE (refund_amount IS NULL) <> (refund_amount_minor IS NULL)').fetchone()[0]


# Agent tools before and after the reader migration.
def tool_get_refund_v1(conn, case_id):
    row = conn.execute('SELECT refund_amount FROM returns WHERE case_id = ?', (case_id,)).fetchone()
    return {'case_id': case_id, OLD: float(row[0])}


def tool_get_refund_v2(conn, case_id):
    row = conn.execute('SELECT refund_amount_minor FROM returns WHERE case_id = ?', (case_id,)).fetchone()
    return {'case_id': case_id, NEW: row[0]}


def tool_set_refund_v1(conn, case_id, pounds):
    conn.execute('UPDATE returns SET refund_amount = ? WHERE case_id = ?', (pounds, case_id))


def tool_set_refund_v2(conn, case_id, pence):
    conn.execute('UPDATE returns SET refund_amount_minor = ? WHERE case_id = ?', (pence, case_id))


def scan_references(root, name=OLD, allow=('migration.py', 'test_migration.py')):
    """Every file under root (prompts, tool schemas, memory notes, eval fixtures) that still uses the old name."""
    pattern = re.compile(r'\b%s\b' % re.escape(name))
    hits = {}
    for path in sorted(Path(root).rglob('*')):
        if path.is_file() and path.name not in allow:
            count = len(pattern.findall(path.read_text(encoding='utf-8', errors='ignore')))
            if count:
                hits[path.relative_to(root).as_posix()] = count
    return hits


def contract_allowed(conn, reference_hits):
    """Drop only when nothing writes the old column and nothing outside the migration mentions it."""
    old_writes = conn.execute('SELECT count(*) FROM migration_old_writes').fetchone()[0]
    reasons = []
    if old_writes:
        reasons.append('%d write(s) still arrive through the old column' % old_writes)
    if reference_hits:
        reasons.append('old name still referenced in: ' + ', '.join(sorted(reference_hits)))
    if half_filled(conn):
        reasons.append('rows with only one column set')
    return (not reasons), reasons


def contract(conn):
    for t in ('returns_sync_insert', 'returns_sync_new', 'returns_sync_old'):
        conn.execute('DROP TRIGGER %s' % t)
    conn.execute('ALTER TABLE returns DROP COLUMN refund_amount')


def demo(fixtures_dir):
    conn = sqlite3.connect(':memory:')
    create(conn)
    expand(conn)
    out = [('batches', backfill(conn)), ('half_filled', half_filled(conn))]
    tool_set_refund_v1(conn, 'CASE-6003', 12.34)
    out.append(('old_tool_write_seen_by_new_reader', tool_get_refund_v2(conn, 'CASE-6003')))
    tool_set_refund_v2(conn, 'CASE-6004', 999)
    out.append(('new_tool_write_seen_by_old_reader', tool_get_refund_v1(conn, 'CASE-6004')))
    hits = scan_references(fixtures_dir)
    out.append(('contract_allowed_before_cleanup', contract_allowed(conn, hits)[0]))
    conn.execute('DELETE FROM migration_old_writes')
    ok, _ = contract_allowed(conn, {})
    out.append(('contract_allowed_after_cleanup', ok))
    contract(conn)
    out.append(('columns_after_contract', [r[1] for r in conn.execute('PRAGMA table_info(returns)')]))
    return out


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    for name, value in demo(here / 'fixtures'):
        print('%-36s %s' % (name, value))
    print('references', scan_references(here / 'fixtures'))
