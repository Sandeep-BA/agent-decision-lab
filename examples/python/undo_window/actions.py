"""Delayed agent actions with an undo window: schedule, cancel, claim and execute, on SQLite.

Author: Sandeep Belgavi. Companion to "An Undo Window Instead of Pre-Approval" (aicassindra.com).
Synthetic Belgavi's Book Store actions. No model and no payment provider are called: the executor records
calls to a fake downstream that deduplicates by idempotency key, as a real refund API should.
"""
import os
import sqlite3
import tempfile
import threading

WINDOW = {"return_label": 120, "refund": 900}   # seconds per action kind


def connect(path):
    conn = sqlite3.connect(path, timeout=10, isolation_level=None, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def setup(path):
    conn = connect(path)
    conn.executescript("""
        CREATE TABLE agent_action (id INTEGER PRIMARY KEY, kind TEXT, payload TEXT, state TEXT NOT NULL,
                                   execute_at INTEGER NOT NULL, cancelled_by TEXT, claimed_at INTEGER);
        CREATE TABLE downstream_call (idempotency_key TEXT PRIMARY KEY, payload TEXT);
    """)
    return conn


def schedule(conn, kind, payload, now):
    cur = conn.execute("INSERT INTO agent_action (kind, payload, state, execute_at) VALUES (?, ?, 'scheduled', ?)",
                       (kind, payload, now + WINDOW[kind]))
    return cur.lastrowid


def cancel(conn, action_id, who):
    row = conn.execute(
        "UPDATE agent_action SET state = 'cancelled', cancelled_by = ? "
        "WHERE id = ? AND state = 'scheduled' RETURNING id", (who, action_id)).fetchone()
    if row:
        return {"result": "cancelled"}
    state = conn.execute("SELECT state FROM agent_action WHERE id = ?", (action_id,)).fetchone()[0]
    return {"result": "too_late", "state": state,
            "next_step": "use the compensating action for this kind of effect"}


def claim_due(conn, now):
    return conn.execute(
        "UPDATE agent_action SET state = 'executing', claimed_at = ? "
        "WHERE id = (SELECT id FROM agent_action WHERE state = 'scheduled' AND execute_at <= ? "
        "ORDER BY execute_at LIMIT 1) AND state = 'scheduled' RETURNING id, kind, payload",
        (now, now)).fetchone()


def execute(conn, claimed):
    """Call the downstream with a key derived from the action id, then mark the action done."""
    action_id, kind, payload = claimed
    key = "agent-action-%d" % action_id
    conn.execute("INSERT OR IGNORE INTO downstream_call VALUES (?, ?)", (key, payload))
    conn.execute("UPDATE agent_action SET state = 'done' WHERE id = ? AND state = 'executing'", (action_id,))
    return key


def race_once(path, now):
    """A person cancels and a worker claims the same due action at the same moment. Returns who won."""
    setup_conn = connect(path)
    action_id = schedule(setup_conn, "refund", "BK-1054 refund 450", now - WINDOW["refund"])
    setup_conn.close()
    barrier = threading.Barrier(2)
    out = {}

    def person():
        c = connect(path)
        barrier.wait()
        out["cancel"] = cancel(c, action_id, "Tanishka")
        c.close()

    def worker():
        c = connect(path)
        barrier.wait()
        claimed = claim_due(c, now)
        out["claim"] = claimed
        if claimed:
            execute(c, claimed)
        c.close()

    threads = [threading.Thread(target=person), threading.Thread(target=worker)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return out


def demo():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "actions.db")
        conn = setup(path)
        a = schedule(conn, "return_label", "BK-1044 return label", now=1000)
        b = schedule(conn, "refund", "BK-1054 refund 450", now=1000)
        print("cancel return label at 1060:", cancel(conn, a, "Tanishka")["result"])
        print("claim at 1060:", claim_due(conn, 1060))
        claimed = claim_due(conn, 1900)
        print("claim at 1900:", claimed[0], claimed[1])
        print("executed with key:", execute(conn, claimed))
        print("cancel refund at 1901:", cancel(conn, b, "Tanishka"))
        conn.close()


if __name__ == "__main__":
    demo()
