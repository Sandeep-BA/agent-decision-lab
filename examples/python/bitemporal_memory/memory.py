"""Bitemporal agent memory in SQLite: valid time and record time, corrections, conflicts and erasure.

Author: Sandeep Belgavi. Companion to "Bitemporal Agent Memory: Recording When a Fact Was True Separately
From When the Agent Learned It" (aicassindra.com, Agents).

The model never writes rows. It proposes (subject, attribute, value, valid_from, source); the functions
below open and close intervals deterministically. Dates are ISO strings, which compare correctly as text.
No model is called; the facts come from fixtures/events.json.
"""
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA = """CREATE TABLE memory (
    subject TEXT, attribute TEXT, value TEXT, source TEXT,
    valid_from TEXT, valid_to TEXT, recorded_from TEXT, recorded_to TEXT)"""


def open_memory():
    db = sqlite3.connect(":memory:")
    db.execute(SCHEMA)
    return db


def believed(db, subject, attribute, valid_at, known_at):
    """What did memory hold, as of known_at, about the world at valid_at? More than one row means a conflict."""
    return db.execute(
        """SELECT value, source FROM memory
           WHERE subject = ? AND attribute = ?
             AND valid_from <= ? AND (valid_to IS NULL OR ? < valid_to)
             AND recorded_from <= ? AND (recorded_to IS NULL OR ? < recorded_to)
           ORDER BY source""",
        (subject, attribute, valid_at, valid_at, known_at, known_at)).fetchall()


def learn(db, subject, attribute, value, valid_from, now, source):
    """Record that value holds from valid_from; earlier rows keep their history."""
    rows = db.execute(
        """SELECT rowid, value, valid_from, valid_to FROM memory
           WHERE subject = ? AND attribute = ? AND recorded_to IS NULL
             AND (valid_to IS NULL OR valid_to > ?)""",
        (subject, attribute, valid_from)).fetchall()
    for rowid, old, vf, vt in rows:
        db.execute("UPDATE memory SET recorded_to = ? WHERE rowid = ?", (now, rowid))
        if vf < valid_from:   # the old value was still true before the change
            db.execute("INSERT INTO memory VALUES (?,?,?,?,?,?,?,NULL)",
                       (subject, attribute, old, source, vf, valid_from, now))
    db.execute("INSERT INTO memory VALUES (?,?,?,?,?,NULL,?,NULL)",
               (subject, attribute, value, source, valid_from, now))


def record_conflict(db, subject, attribute, value, valid_from, now, source):
    """Add a competing claim without closing existing beliefs; both stay current with their sources."""
    db.execute("INSERT INTO memory VALUES (?,?,?,?,?,NULL,?,NULL)",
               (subject, attribute, value, source, valid_from, now))


def erase(db, subject, now):
    """Erasure deletes every row about the subject, history included, and keeps only a marker."""
    n = db.execute("DELETE FROM memory WHERE subject = ?", (subject,)).rowcount
    db.execute("INSERT INTO memory VALUES (?,?,?,?,?,NULL,?,NULL)",
               (subject, "erased", "yes", "erasure request", now, now))
    return n


def replay(events):
    db = open_memory()
    for e in events:
        if e["kind"] == "learn":
            learn(db, e["subject"], e["attribute"], e["value"], e["valid_from"], e["at"], e["source"])
        elif e["kind"] == "conflict":
            record_conflict(db, e["subject"], e["attribute"], e["value"], e["valid_from"], e["at"], e["source"])
    return db


if __name__ == "__main__":
    events = json.loads((HERE / "fixtures" / "events.json").read_text(encoding="utf-8"))
    db = replay(events)
    s, a = "customer-88", "shipping_address"
    print(json.dumps({
        "now": believed(db, s, a, "2026-10-27", "2026-10-27"),
        "applied_to_order_of_5_oct_as_known_now": believed(db, s, a, "2026-10-05", "2026-10-27"),
        "agent_believed_on_7_oct": believed(db, s, a, "2026-10-07", "2026-10-07"),
        "rows": db.execute("SELECT COUNT(*) FROM memory").fetchone()[0]}, indent=1))
    sys.exit(0)
