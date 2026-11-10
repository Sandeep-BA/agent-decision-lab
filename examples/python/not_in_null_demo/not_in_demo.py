"""NOT IN versus NOT EXISTS when the subquery returns a NULL.

Author: Sandeep Belgavi. Runs against an in-memory SQLite database from the Python standard
library. PostgreSQL documents the same NOT IN rule; this script does not run PostgreSQL.
"""
import sqlite3

SCHEMA = """
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE returns (id INTEGER PRIMARY KEY, customer_id INTEGER, reason TEXT);
INSERT INTO customers VALUES (1, 'Geetha'), (2, 'Jenya'), (3, 'Tanishka'), (4, 'Dinky');
INSERT INTO returns VALUES (10, 2, 'damaged'), (11, NULL, 'guest checkout'), (12, 3, 'wrong edition');
"""

QUERIES = {
    'not_in': "SELECT name FROM customers WHERE id NOT IN (SELECT customer_id FROM returns) ORDER BY id",
    'not_in_filtered': ("SELECT name FROM customers WHERE id NOT IN "
                        "(SELECT customer_id FROM returns WHERE customer_id IS NOT NULL) ORDER BY id"),
    'not_exists': ("SELECT c.name FROM customers c WHERE NOT EXISTS "
                   "(SELECT 1 FROM returns r WHERE r.customer_id = c.id) ORDER BY c.id"),
    'anti_join': ("SELECT c.name FROM customers c LEFT JOIN returns r ON r.customer_id = c.id "
                  "WHERE r.id IS NULL ORDER BY c.id"),
    'predicate_value': "SELECT 1 NOT IN (2, NULL), 2 NOT IN (2, NULL), 1 NOT IN (2, 3)",
}


def connect():
    db = sqlite3.connect(':memory:')
    db.executescript(SCHEMA)
    return db


def run_all():
    db = connect()
    out = {}
    for name, sql in QUERIES.items():
        rows = db.execute(sql).fetchall()
        out[name] = rows if name == 'predicate_value' else [r[0] for r in rows]
    db.close()
    return out


if __name__ == '__main__':
    for name, rows in run_all().items():
        print(f'{name}: {rows}')
