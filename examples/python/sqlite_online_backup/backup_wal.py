"""Back up a live WAL-mode SQLite database and verify the restore. Author: Sandeep Belgavi.

Synthetic data: book orders at the fictional Belgavi's Book Store. Everything
runs in a temporary directory with Python's bundled sqlite3; nothing else is
touched. The script measures four ways to take a copy while a connection
holds committed but not-yet-checkpointed changes in the -wal file:

1. copy only the main database file (the common mistake)
2. Connection.backup() into a new file
3. VACUUM INTO a new file
4. Connection.backup() while another connection keeps committing
"""
import hashlib
import shutil
import sqlite3
import tempfile
from pathlib import Path


def fingerprint(conn):
    rows = conn.execute('SELECT id, customer, total_paise FROM orders ORDER BY id').fetchall()
    digest = hashlib.sha256(repr(rows).encode()).hexdigest()[:16]
    return len(rows), digest


def open_copy(path):
    conn = sqlite3.connect(path)
    try:
        ok = conn.execute('PRAGMA integrity_check').fetchone()[0]
        try:
            count, digest = fingerprint(conn)
        except sqlite3.OperationalError as e:
            return {'integrity': ok, 'rows': None, 'error': str(e)}
        return {'integrity': ok, 'rows': count, 'sha': digest}
    finally:
        conn.close()


def build(workdir):
    db = workdir / 'orders.db'
    writer = sqlite3.connect(db, isolation_level=None)
    writer.execute('PRAGMA journal_mode=WAL')
    writer.execute('PRAGMA wal_autocheckpoint=0')  # keep later commits in the -wal file
    writer.execute('CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT NOT NULL, total_paise INTEGER NOT NULL)')
    names = ['Geetha', 'Jenya', 'Tanishka', 'Dinky', 'Hansini']
    writer.execute('BEGIN')
    for i in range(1, 101):
        writer.execute('INSERT INTO orders VALUES (?, ?, ?)', (i, names[i % 5], 49_900 + i))
    writer.execute('COMMIT')
    writer.execute('PRAGMA wal_checkpoint(TRUNCATE)')  # first 100 rows now live in orders.db itself
    writer.execute('BEGIN')
    for i in range(101, 151):
        writer.execute('INSERT INTO orders VALUES (?, ?, ?)', (i, names[i % 5], 49_900 + i))
    writer.execute('COMMIT')  # committed, but only in orders.db-wal
    return db, writer


def run(workdir):
    workdir = Path(workdir)
    db, writer = build(workdir)
    result = {'source': dict(zip(('rows', 'sha'), fingerprint(writer))),
              'wal_bytes': (workdir / 'orders.db-wal').stat().st_size}

    shutil.copyfile(db, workdir / 'copied_main_only.db')
    result['copy_main_file'] = open_copy(workdir / 'copied_main_only.db')

    target = sqlite3.connect(workdir / 'backup_api.db')
    writer.backup(target)
    target.close()
    result['backup_api'] = open_copy(workdir / 'backup_api.db')

    writer.execute('VACUUM INTO ?', (str(workdir / 'vacuum_into.db'),))
    result['vacuum_into'] = open_copy(workdir / 'vacuum_into.db')

    # A second connection keeps committing while a paged backup runs on the first.
    other = sqlite3.connect(db, isolation_level=None)
    calls = []
    next_id = [151]

    def progress(status, remaining, total):
        calls.append((remaining, total))
        if next_id[0] <= 153:
            other.execute('INSERT INTO orders VALUES (?, ?, ?)', (next_id[0], 'Geetha', 59_900))
            next_id[0] += 1

    target = sqlite3.connect(workdir / 'backup_during_writes.db')
    writer.backup(target, pages=1, progress=progress, sleep=0)
    target.close()
    other.close()
    result['backup_during_writes'] = open_copy(workdir / 'backup_during_writes.db')
    result['backup_during_writes']['progress_calls'] = len(calls)
    result['source_after_writes'] = dict(zip(('rows', 'sha'), fingerprint(writer)))
    writer.close()
    return result


def main():
    with tempfile.TemporaryDirectory() as d:
        r = run(d)
    print('sqlite', sqlite3.sqlite_version)
    for k, v in r.items():
        print(f'{k}: {v}')


if __name__ == '__main__':
    main()
