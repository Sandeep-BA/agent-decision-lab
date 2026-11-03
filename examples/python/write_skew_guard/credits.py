"""Goodwill credits with a monthly limit: an unguarded read-then-insert tool pair, and a guarded write tool.

Author: Sandeep Belgavi. Companion to "Write Skew Between Concurrent Agent Runs" (aicassindra.com).
Synthetic Belgavi's Book Store data on SQLite. No model is called: two threads stand in for two agent runs.
"""
import os
import sqlite3
import tempfile
import threading

LIMIT = 2
MONTH = "2026-11"


def connect(path):
    conn = sqlite3.connect(path, timeout=10, isolation_level=None, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def setup(path, existing=1, seed_quota=True):
    conn = connect(path)
    conn.executescript("""
        CREATE TABLE goodwill_credit (id INTEGER PRIMARY KEY, customer_id TEXT, case_id TEXT, amount INTEGER, month TEXT);
        CREATE TABLE goodwill_quota (customer_id TEXT, month TEXT, used INTEGER NOT NULL,
                                     PRIMARY KEY (customer_id, month));
    """)
    for i in range(existing):
        conn.execute("INSERT INTO goodwill_credit (customer_id, case_id, amount, month) VALUES (?, ?, ?, ?)",
                     ("geetha", "CASE-40%02d" % i, 200, MONTH))
    if seed_quota:
        conn.execute("INSERT INTO goodwill_quota VALUES (?, ?, ?)", ("geetha", MONTH, existing))
    conn.close()


def list_goodwill_credits(conn, customer_id):
    """Read tool: advice for the agent, never a guarantee."""
    return conn.execute("SELECT count(*) FROM goodwill_credit WHERE customer_id = ? AND month = ?",
                        (customer_id, MONTH)).fetchone()[0]


def grant_unguarded(conn, customer_id, case_id, amount):
    """Write tool as first shipped: inserts whatever the agent decided."""
    conn.execute("INSERT INTO goodwill_credit (customer_id, case_id, amount, month) VALUES (?, ?, ?, ?)",
                 (customer_id, case_id, amount, MONTH))
    return {"status": "granted"}


def grant_guarded(conn, customer_id, case_id, amount, limit=LIMIT):
    """Write tool with the limit enforced in one short transaction on a quota row."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        # Start the quota row from the credits that already exist, so switching tools mid-month counts them.
        conn.execute("INSERT OR IGNORE INTO goodwill_quota SELECT ?, ?, count(*) FROM goodwill_credit "
                     "WHERE customer_id = ? AND month = ?", (customer_id, MONTH, customer_id, MONTH))
        row = conn.execute("UPDATE goodwill_quota SET used = used + 1 "
                           "WHERE customer_id = ? AND month = ? AND used < ? RETURNING used",
                           (customer_id, MONTH, limit)).fetchone()
        if row is None:
            conn.execute("COMMIT")
            return {"status": "limit_reached", "limit": limit, "month": MONTH,
                    "next_step": "explain the limit or hand the case to a person"}
        conn.execute("INSERT INTO goodwill_credit (customer_id, case_id, amount, month) VALUES (?, ?, ?, ?)",
                     (customer_id, case_id, amount, MONTH))
        conn.execute("COMMIT")
        return {"status": "granted", "used": row[0], "limit": limit}
    except Exception:
        conn.execute("ROLLBACK")
        raise


def race(grant, path, cases=("CASE-4101", "CASE-4102")):
    """Each 'run' reads the count, waits at a barrier so all have read, then calls the write tool."""
    barrier = threading.Barrier(len(cases))
    results = {}

    def run(case_id):
        conn = connect(path)
        seen = list_goodwill_credits(conn, "geetha")
        barrier.wait()
        results[case_id] = grant(conn, "geetha", case_id, 300) if seen < LIMIT else {"status": "not attempted"}
        conn.close()

    threads = [threading.Thread(target=run, args=(c,)) for c in cases]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    conn = connect(path)
    total = list_goodwill_credits(conn, "geetha")
    conn.close()
    return total, results


def demo():
    for name, grant in (("unguarded", grant_unguarded), ("guarded", grant_guarded)):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "credits.db")
            setup(path, existing=1)
            total, results = race(grant, path)
            statuses = sorted(r["status"] for r in results.values())
            print("%-9s credits=%d limit=%d results=%s" % (name, total, LIMIT, statuses))


if __name__ == "__main__":
    demo()
