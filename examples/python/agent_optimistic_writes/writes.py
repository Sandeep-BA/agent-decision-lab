"""Agent writes without lost updates: a version-checked field merge with coupled field groups.

Author: Sandeep Belgavi. Companion to "Agents and Lost Updates: Version Checks, Re-Planning on Conflict and
Field Merges When Think Time Is Seconds" (aicassindra.com). Uses an in-memory SQLite table and a fixed
interleaving of an agent and a person; no model is called.
"""
import json
import sqlite3

COUPLED = [{"status", "priority"}, {"amount", "currency"}]


def connect():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE tickets (id TEXT PRIMARY KEY, version INTEGER, data TEXT)")
    return db


def read_ticket(db, ticket_id):
    version, data = db.execute("SELECT version, data FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return version, json.loads(data)


def write_unconditional(db, ticket_id, record):
    """The anti-pattern: write the whole record the agent read, with its changes applied."""
    db.execute("UPDATE tickets SET data = ?, version = version + 1 WHERE id = ?", (json.dumps(record), ticket_id))


def write_ticket(db, ticket_id, read_version, base, changes):
    """Apply an agent's field changes if they merge with what changed since it read."""
    row = db.execute("SELECT version, data FROM tickets WHERE id = ?",
                     (ticket_id,)).fetchone()
    version, current = row[0], json.loads(row[1])
    if version != read_version:
        theirs = {k for k in current if current.get(k) != base.get(k)}
        ours = set(changes)
        touched = ours | {f for g in COUPLED if g & ours for f in g}
        if theirs & touched:
            return {"status": "conflict", "current_version": version,
                    "changed_since_read": sorted(theirs), "current": current}
    merged = {**current, **changes}
    cur = db.execute(
        "UPDATE tickets SET data = ?, version = version + 1 "
        "WHERE id = ? AND version = ?",
        (json.dumps(merged), ticket_id, version))
    if cur.rowcount == 0:          # someone wrote between our SELECT and UPDATE
        return {"status": "conflict", "current_version": None}
    return {"status": "ok", "version": version + 1}


def seed(db):
    db.execute("INSERT INTO tickets VALUES (?, ?, ?)",
               ("T-4471", 7, json.dumps({"status": "open", "priority": "P3", "note": "", "summary": ""})))


def person_escalates(db):
    """The person's edit lands while the agent is thinking (version 7 -> 8)."""
    version, rec = read_ticket(db, "T-4471")
    rec.update(priority="P1", note="Customer is a hospital")
    db.execute("UPDATE tickets SET data = ?, version = ? WHERE id = ?", (json.dumps(rec), version + 1, "T-4471"))


def scenario(strategy):
    db = connect(); seed(db)
    read_version, base = read_ticket(db, "T-4471")           # agent reads version 7
    person_escalates(db)                                      # 8 seconds later
    if strategy == "unconditional":
        write_unconditional(db, "T-4471", {**base, "status": "resolved", "summary": "Duplicate charge refunded"})
        result = {"status": "ok"}
    elif strategy == "status_and_summary":
        result = write_ticket(db, "T-4471", read_version, base, {"status": "resolved", "summary": "Duplicate charge refunded"})
    elif strategy == "summary_only":
        result = write_ticket(db, "T-4471", read_version, base, {"summary": "Duplicate charge refunded"})
    else:
        raise ValueError(strategy)
    return result, read_ticket(db, "T-4471")


def main():
    for strategy in ("unconditional", "status_and_summary", "summary_only"):
        result, (version, record) = scenario(strategy)
        print(strategy, json.dumps(result.get("status")), json.dumps(result.get("changed_since_read")), version, json.dumps(record))


if __name__ == "__main__":
    main()
