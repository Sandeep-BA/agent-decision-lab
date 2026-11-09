"""Durable-boundary fixture for a refund note. Author: Sandeep Belgavi.

SQLite stands in for the effect service; this does not test a remote provider.
"""
import hashlib, os, sqlite3, sys, uuid
from contextlib import closing
from pathlib import Path

CASE = 'CASE-0017'
POINTS = ('before_plan', 'after_plan', 'before_effect', 'after_effect', 'after_complete')


def run(database, crash='none', unsafe=False):
    """Run or resume one case. unsafe=True mints a new operation id on every attempt."""
    with closing(sqlite3.connect(database)) as db, db:
        db.executescript('CREATE TABLE IF NOT EXISTS task (id TEXT PRIMARY KEY, payload TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0); '
                         'CREATE TABLE IF NOT EXISTS effect (operation TEXT PRIMARY KEY, digest TEXT NOT NULL, value TEXT NOT NULL);')
    if crash == 'before_plan':
        os._exit(17)
    with closing(sqlite3.connect(database)) as db, db:
        db.execute('INSERT OR IGNORE INTO task(id,payload) VALUES(?,?)', (CASE, 'synthetic refund note'))
    if crash == 'after_plan':
        os._exit(17)
    with closing(sqlite3.connect(database)) as db, db:
        payload = db.execute('SELECT payload FROM task WHERE id=?', (CASE,)).fetchone()[0]
    if crash == 'before_effect':
        os._exit(17)
    with closing(sqlite3.connect(database)) as db, db:
        value = payload.upper()
        digest = hashlib.sha256(value.encode()).hexdigest()
        operation = f'{CASE}:refund-note:' + (uuid.uuid4().hex if unsafe else 'v1')
        db.execute('INSERT OR IGNORE INTO effect VALUES(?,?,?)', (operation, digest, value))
        stored = db.execute('SELECT digest FROM effect WHERE operation=?', (operation,)).fetchone()[0]
        if stored != digest:
            raise ValueError('conflicting payload under operation identifier')
    if crash == 'after_effect':
        os._exit(17)
    with closing(sqlite3.connect(database)) as db, db:
        db.execute('UPDATE task SET done=1 WHERE id=? AND payload=?', (CASE, payload))
    if crash == 'after_complete':
        os._exit(17)


if __name__ == '__main__':
    run(Path(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else 'none', len(sys.argv) > 3 and sys.argv[3] == 'unsafe')
