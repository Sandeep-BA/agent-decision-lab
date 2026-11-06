"""Holding the last copy while a model thinks: a long transaction versus an expiring hold, on SQLite.

Author: Sandeep Belgavi. Companion to "Holding a Row Lock While the Model Thinks" (aicassindra.com).
Standard library only. The "model" is a fake that sleeps; nothing is called over the network.

SQLite locks the whole database for a write transaction (BEGIN IMMEDIATE), which is coarser than a PostgreSQL
row lock, so the long-transaction design is even more expensive here. The hold design behaves the same way on
both: two short transactions with the slow step between them.
"""
import sqlite3
import threading
import time

SKU = 'SFE-0017'


def connect(path, busy_ms=10000):
    conn = sqlite3.connect(path, timeout=busy_ms / 1000, isolation_level=None, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def setup(path, copies=1):
    c = connect(path)
    c.executescript('''
        DROP TABLE IF EXISTS titles; DROP TABLE IF EXISTS holds;
        CREATE TABLE titles (sku TEXT PRIMARY KEY, available INTEGER NOT NULL CHECK (available >= 0));
        CREATE TABLE holds (hold_id TEXT PRIMARY KEY, sku TEXT NOT NULL, case_id TEXT NOT NULL,
                            state TEXT NOT NULL, expires_at REAL NOT NULL);
        CREATE UNIQUE INDEX one_live_hold ON holds (case_id, sku) WHERE state = 'held';
    ''')
    c.execute('INSERT INTO titles VALUES (?, ?)', (SKU, copies))
    c.close()


def long_transaction_step(path, case_id, think, model):
    """The design the article warns against: the model call happens inside the write transaction."""
    c = connect(path)
    c.execute('BEGIN IMMEDIATE')                     # takes the write lock now
    (available,) = c.execute('SELECT available FROM titles WHERE sku = ?', (SKU,)).fetchone()
    if available <= 0:
        c.execute('COMMIT'); c.close(); return 'none_available'
    model(think)                                     # the transaction stays open for the whole call
    c.execute('UPDATE titles SET available = available - 1 WHERE sku = ?', (SKU,))
    c.execute('COMMIT'); c.close()
    return 'swapped'


def hold(path, case_id, ttl, now=time.time):
    c = connect(path)
    c.execute('BEGIN IMMEDIATE')
    cur = c.execute('UPDATE titles SET available = available - 1 WHERE sku = ? AND available > 0', (SKU,))
    if cur.rowcount == 0:
        c.execute('COMMIT'); c.close(); return None
    hold_id = 'h-' + case_id
    c.execute("INSERT INTO holds VALUES (?, ?, ?, 'held', ?)", (hold_id, SKU, case_id, now() + ttl))
    c.execute('COMMIT'); c.close()
    return hold_id


def confirm(path, hold_id, now=time.time):
    c = connect(path)
    cur = c.execute("UPDATE holds SET state = 'confirmed' WHERE hold_id = ? AND state = 'held' AND expires_at > ?",
                    (hold_id, now()))
    c.close()
    return 'confirmed' if cur.rowcount == 1 else 'hold_expired'


def sweep(path, now=time.time):
    """Return expired holds to stock. Same conditional transition as confirm, so only one of them can win."""
    c = connect(path)
    c.execute('BEGIN IMMEDIATE')
    rows = c.execute("SELECT hold_id FROM holds WHERE state = 'held' AND expires_at <= ?", (now(),)).fetchall()
    for (hold_id,) in rows:
        if c.execute("UPDATE holds SET state = 'expired' WHERE hold_id = ? AND state = 'held'", (hold_id,)).rowcount:
            c.execute('UPDATE titles SET available = available + 1 WHERE sku = ?', (SKU,))
    c.execute('COMMIT'); c.close()
    return len(rows)


def hold_step(path, case_id, think, model, ttl=600):
    hold_id = hold(path, case_id, ttl)
    if hold_id is None:
        return 'none_available'
    model(think)                                     # no transaction is open here
    return confirm(path, hold_id)


def checkout(path):
    """A website checkout: one short conditional update. Returns (result, seconds waited)."""
    c = connect(path)
    t0 = time.perf_counter()
    cur = c.execute('UPDATE titles SET available = available - 1 WHERE sku = ? AND available > 0', (SKU,))
    waited = time.perf_counter() - t0
    c.close()
    return ('sold' if cur.rowcount else 'sold_out'), waited


def race(path, design, think=1.0, start_checkout_after=0.2):
    """Run one agent step and one checkout that starts while the model is thinking."""
    setup(path)
    out = {}
    step = long_transaction_step if design == 'long' else hold_step
    t = threading.Thread(target=lambda: out.__setitem__('agent', step(path, 'CASE-5120', think, time.sleep)))
    t.start()
    time.sleep(start_checkout_after)
    out['checkout'], out['checkout_wait_s'] = checkout(path)
    t.join()
    return out


if __name__ == '__main__':
    import json, os, tempfile
    d = tempfile.mkdtemp()
    for design in ('long', 'hold'):
        r = race(os.path.join(d, design + '.db'), design)
        r['checkout_wait_s'] = round(r['checkout_wait_s'], 1)
        print(design, json.dumps(r))
