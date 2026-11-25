"""Author: Sandeep Belgavi. PostgreSQL 18 virtual vs stored generated columns, checked
statement by statement against a disposable database. Each step states the outcome it
expects (ok, or the SQLSTATE class name psycopg raises); any mismatch exits non-zero."""
import json
import os
import sys
import psycopg

STEPS = [
    ("DROP TABLE IF EXISTS book_order_lines", "ok"),
    ("""CREATE TABLE book_order_lines (
          id bigint PRIMARY KEY,
          quantity int NOT NULL,
          unit_price_cents int NOT NULL,
          title text NOT NULL,
          line_total_cents int GENERATED ALWAYS AS (quantity * unit_price_cents),
          title_key text GENERATED ALWAYS AS (lower(title)) STORED)""", "ok"),
    ("""SELECT attname, attgenerated FROM pg_attribute
        WHERE attrelid = 'book_order_lines'::regclass AND attgenerated <> '' ORDER BY attnum""", "ok"),
    ("""INSERT INTO book_order_lines (id, quantity, unit_price_cents, title)
        VALUES (1, 2, 1250, 'Distributed Systems Notes'), (2, 1, 3999, 'Kafka Field Guide')""", "ok"),
    ("SELECT id, line_total_cents, title_key FROM book_order_lines ORDER BY id", "ok"),
    ("""INSERT INTO book_order_lines (id, quantity, unit_price_cents, title, line_total_cents)
        VALUES (3, 1, 100, 'x', 100)""", "GeneratedAlways"),
    ("CREATE INDEX ON book_order_lines (line_total_cents)", "FeatureNotSupported"),
    ("CREATE INDEX line_total_expr ON book_order_lines ((quantity * unit_price_cents))", "ok"),
    ("CREATE UNIQUE INDEX title_key_unique ON book_order_lines (title_key)", "ok"),
    ("SET enable_seqscan = off", "ok"),
    ("EXPLAIN (COSTS OFF) SELECT id FROM book_order_lines WHERE line_total_cents > 3000", "ok"),
    ("RESET enable_seqscan", "ok"),
    ("CREATE STATISTICS lt_stats ON line_total_cents FROM book_order_lines", "FeatureNotSupported"),
    ("CREATE STATISTICS lt_expr_stats ON (quantity * unit_price_cents) FROM book_order_lines", "ok"),
    ("ALTER TABLE book_order_lines ADD CONSTRAINT positive_total CHECK (line_total_cents > 0)", "ok"),
    ("""INSERT INTO book_order_lines (id, quantity, unit_price_cents, title)
        VALUES (4, 0, 500, 'Zero Copy')""", "CheckViolation"),
    ("ALTER TABLE book_order_lines ALTER COLUMN line_total_cents SET EXPRESSION AS (quantity * unit_price_cents)",
     "FeatureNotSupported"),
    ("ALTER TABLE book_order_lines ALTER COLUMN line_total_cents DROP EXPRESSION", "FeatureNotSupported"),
    ("ALTER TABLE book_order_lines ALTER COLUMN title_key SET EXPRESSION AS (upper(title))", "ok"),
    ("SELECT id, title_key FROM book_order_lines ORDER BY id", "ok"),
    ("CREATE OR REPLACE FUNCTION add_tax(int) RETURNS int IMMUTABLE LANGUAGE sql AS 'SELECT $1 * 118 / 100'", "ok"),
    ("CREATE TABLE tax_virtual (a int, b int GENERATED ALWAYS AS (add_tax(a)) VIRTUAL)", "FeatureNotSupported"),
    ("CREATE TABLE tax_stored (a int, b int GENERATED ALWAYS AS (add_tax(a)) STORED)", "ok"),
    ("DROP TABLE IF EXISTS tax_stored", "ok"),
    ("DROP FUNCTION add_tax(int)", "ok"),
]

results, failed = [], 0
with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
    version = conn.execute("SHOW server_version").fetchone()[0]
    for sql, expected in STEPS:
        try:
            cur = conn.execute(sql)
            outcome = "ok"
            rows = [list(r) for r in cur.fetchall()] if cur.description else None
        except psycopg.Error as e:
            outcome, rows = type(e).__name__, str(e).splitlines()[0]
        if outcome != expected:
            failed += 1
        results.append({"sql": " ".join(sql.split())[:120], "expected": expected, "outcome": outcome, "rows": rows})
print(json.dumps({"server_version": version, "failed": failed, "steps": results}, indent=1))
sys.exit(1 if failed else 0)
