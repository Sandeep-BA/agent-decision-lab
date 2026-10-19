"""Agent tool effects through a transactional outbox, on SQLite.

Author: Sandeep Belgavi. Teaching model with synthetic data; no model provider is called.

One run (R-91) executes a three-step plan. Step 2, issue_refund, has effects: the handler
writes the refund row, the step journal row and the outbox row in one transaction. A relay
publishes unpublished outbox rows to an in-memory broker; a consumer posts each delivered
event to a ledger table, deduplicating on the outbox id. Fault injection chooses where a
process dies.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

FIXTURE = Path(__file__).with_name("fixtures") / "run_r91.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS refunds (id INTEGER PRIMARY KEY, order_id TEXT, amount INTEGER, issued_by TEXT);
CREATE TABLE IF NOT EXISTS step_journal (run_id TEXT, step_index INTEGER, attempt INTEGER, tool TEXT, result TEXT,
                                         PRIMARY KEY (run_id, step_index, attempt));
CREATE TABLE IF NOT EXISTS outbox (id INTEGER PRIMARY KEY, run_id TEXT, step_index INTEGER, topic TEXT,
                                   payload TEXT, published INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS processed (outbox_id INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS ledger_entries (id INTEGER PRIMARY KEY, outbox_id INTEGER, amount INTEGER);
"""


class Crash(Exception):
    """Raised by fault injection where a process would die."""


@dataclass
class Settings:
    atomic: bool = True
    step_key: bool = True
    consumer_dedup: bool = True
    relay_order: str = "publish_then_mark"   # or "mark_then_publish"
    resume: bool = True
    crash_at: str = "none"                   # none | before_commit | after_commit | relay_between
    agent_retry: bool = False


@dataclass
class World:
    """All the stores of the model plus a trace."""
    db: sqlite3.Connection
    settings: Settings
    broker: list[dict] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    tool_calls: int = 0
    resumes: int = 0
    _crashed: set[str] = field(default_factory=set)

    def crash_once(self, point: str) -> None:
        if self.settings.crash_at == point and point not in self._crashed:
            self._crashed.add(point)
            self.trace.append(f"CRASH at {point}")
            raise Crash(point)


def open_world(settings: Settings, path: str | None = None) -> World:
    db = sqlite3.connect(path or os.environ.get("OUTBOX_DB_PATH", ":memory:"))
    db.isolation_level = None            # explicit BEGIN/COMMIT below
    db.executescript(SCHEMA)
    return World(db=db, settings=settings)


def journaled(world: World, run_id: str, step_index: int):
    row = world.db.execute("SELECT result FROM step_journal WHERE run_id=? AND step_index=? ORDER BY attempt",
                           (run_id, step_index)).fetchone()
    return json.loads(row[0]) if row else None


def next_attempt(world: World, run_id: str, step_index: int) -> int:
    """Without a step key the runtime journals every attempt as its own row; with one, only the first ever lands."""
    n = world.db.execute("SELECT COUNT(*) FROM step_journal WHERE run_id=? AND step_index=?",
                         (run_id, step_index)).fetchone()[0]
    return n + 1


def issue_refund(world: World, run_id: str, step_index: int, order_id: str, amount: int, label: str) -> dict:
    """The effecting tool handler. Returns the result the agent would receive."""
    s, db = world.settings, world.db
    world.tool_calls += 1
    if s.step_key:
        prior = journaled(world, run_id, step_index)
        if prior is not None:
            world.trace.append(f"{label}: step key {run_id}:{step_index} found the journal row; no new effect")
            return prior
    attempt = next_attempt(world, run_id, step_index)
    if s.atomic:
        db.execute("BEGIN")
        try:
            cur = db.execute("INSERT INTO refunds(order_id, amount, issued_by) VALUES (?,?,?)",
                             (order_id, amount, label))
            result = {"refund_id": cur.lastrowid, "amount": amount}
            world.crash_once("before_commit")   # rolls back everything below and above
            db.execute("INSERT INTO step_journal VALUES (?,?,?,?,?)",
                       (run_id, step_index, attempt, "issue_refund", json.dumps(result)))
            db.execute("INSERT INTO outbox(run_id, step_index, topic, payload) VALUES (?,?,?,?)",
                       (run_id, step_index, "refund.issued", json.dumps(result)))
            db.execute("COMMIT")
        except Crash:
            db.execute("ROLLBACK")
            raise
        world.trace.append(f"{label}: refund, journal and outbox committed together")
    else:
        cur = db.execute("INSERT INTO refunds(order_id, amount, issued_by) VALUES (?,?,?)",
                         (order_id, amount, label))
        result = {"refund_id": cur.lastrowid, "amount": amount}
        world.crash_once("before_commit")       # the refund row survives on its own
        db.execute("INSERT INTO step_journal VALUES (?,?,?,?,?)",
                   (run_id, step_index, attempt, "issue_refund", json.dumps(result)))
        db.execute("INSERT INTO outbox(run_id, step_index, topic, payload) VALUES (?,?,?,?)",
                   (run_id, step_index, "refund.issued", json.dumps(result)))
        world.trace.append(f"{label}: three separate writes")
    world.crash_once("after_commit")            # all rows exist, the agent never sees the answer
    return result


def run_agent(world: World, plan: dict, label: str = "first run") -> None:
    """A fixed policy: executes the plan in order and retries a call it saw no answer for."""
    run_id = plan["run_id"]
    for step in plan["steps"]:
        idx = step["index"]
        if world.settings.resume and journaled(world, run_id, idx) is not None:
            world.trace.append(f"{label}: step {idx} already journaled, skipped")
            continue
        if step["tool"] == "lookup_order":
            world.db.execute("INSERT OR REPLACE INTO step_journal VALUES (?,?,1,?,?)",
                             (run_id, idx, "lookup_order", json.dumps({"order_id": step["order_id"]})))
            world.trace.append(f"{label}: step {idx} lookup_order (read-only) journaled after the fact")
        elif step["tool"] == "issue_refund":
            issue_refund(world, run_id, idx, step["order_id"], step["amount"], f"{label} call")
            if world.settings.agent_retry:
                world.trace.append(f"{label}: tool call timed out from the agent side; retrying")
                issue_refund(world, run_id, idx, step["order_id"], step["amount"], f"{label} retry")
        elif step["tool"] == "notify":
            world.trace.append(f"{label}: step {idx} notify is carried by the outbox event; nothing to do here")


def run_with_recovery(world: World, plan: dict) -> None:
    try:
        run_agent(world, plan)
    except Crash:
        if world.settings.resume:
            world.resumes += 1
            world.trace.append("resume: loading run from the journal")
            run_agent(world, plan, label="resumed run")
        else:
            world.trace.append("restart: no resume, the run starts from scratch")
            # a restart does not consult the journal for skipping; the step key is the only defence
            saved = world.settings.resume
            run_agent(world, plan, label="restarted run")
            world.settings.resume = saved


def relay_once(world: World) -> int:
    """Publishes unpublished outbox rows. Order decides the delivery semantics."""
    db, s = world.db, world.settings
    rows = db.execute("SELECT id, topic, payload FROM outbox WHERE published=0 ORDER BY id").fetchall()
    for oid, topic, payload in rows:
        if s.relay_order == "publish_then_mark":
            world.broker.append({"outbox_id": oid, "topic": topic, **json.loads(payload)})
            try:
                world.crash_once("relay_between")
            except Crash:
                world.trace.append(f"relay: published {oid}, died before marking; it will be republished")
                return len(rows)
            db.execute("UPDATE outbox SET published=1 WHERE id=?", (oid,))
        else:
            db.execute("UPDATE outbox SET published=1 WHERE id=?", (oid,))
            try:
                world.crash_once("relay_between")
            except Crash:
                world.trace.append(f"relay: marked {oid} published, died before publishing; the event is lost")
                return len(rows)
            world.broker.append({"outbox_id": oid, "topic": topic, **json.loads(payload)})
    return len(rows)


def consume_all(world: World) -> None:
    db, s = world.db, world.settings
    for msg in world.broker:
        if s.consumer_dedup:
            db.execute("BEGIN")
            cur = db.execute("INSERT OR IGNORE INTO processed(outbox_id) VALUES (?)", (msg["outbox_id"],))
            if cur.rowcount == 0:
                db.execute("COMMIT")
                world.trace.append(f"consumer: outbox {msg['outbox_id']} already processed; ignored")
                continue
            db.execute("INSERT INTO ledger_entries(outbox_id, amount) VALUES (?,?)",
                       (msg["outbox_id"], msg["amount"]))
            db.execute("COMMIT")
        else:
            db.execute("INSERT INTO ledger_entries(outbox_id, amount) VALUES (?,?)",
                       (msg["outbox_id"], msg["amount"]))
        world.trace.append(f"consumer: posted {msg['amount']} for outbox {msg['outbox_id']}")


def report(world: World) -> dict:
    db = world.db
    refunds = db.execute("SELECT COUNT(*) FROM refunds").fetchone()[0]
    journal = db.execute("SELECT COUNT(*) FROM step_journal").fetchone()[0]
    outbox = db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
    ledger = db.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]
    distinct_ledger = db.execute("SELECT COUNT(DISTINCT outbox_id) FROM ledger_entries").fetchone()[0]
    delivered_ids = {m["outbox_id"] for m in world.broker}
    return {
        "refunds": refunds, "journal_steps": journal, "outbox_rows": outbox,
        "deliveries": len(world.broker), "ledger_entries": ledger,
        "duplicate_refunds": max(0, refunds - 1),
        "lost_events": max(0, refunds - len(delivered_ids)),
        "duplicate_postings": ledger - distinct_ledger,
        "tool_calls": world.tool_calls, "resumes": world.resumes,
    }


def simulate(settings: Settings, plan: dict | None = None) -> tuple[dict, list[str]]:
    plan = plan or json.loads(FIXTURE.read_text(encoding="utf-8"))
    world = open_world(settings)
    run_with_recovery(world, plan)
    relay_once(world)
    relay_once(world)          # a second pass models the next relay tick after a relay crash
    consume_all(world)
    return report(world), world.trace


SCENARIOS = {
    "clean": {},
    "crash-before-commit": {"crash_at": "before_commit"},
    "crash-after-commit": {"crash_at": "after_commit"},
    "relay-crash": {"crash_at": "relay_between"},
    "agent-retry": {"agent_retry": True},
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenario", choices=sorted(SCENARIOS), default="clean")
    ap.add_argument("--no-atomic", action="store_true")
    ap.add_argument("--no-step-key", action="store_true")
    ap.add_argument("--no-dedup", action="store_true")
    ap.add_argument("--mark-first", action="store_true", help="relay marks published before publishing")
    ap.add_argument("--no-resume", action="store_true")
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()
    s = Settings(atomic=not a.no_atomic, step_key=not a.no_step_key, consumer_dedup=not a.no_dedup,
                 relay_order="mark_then_publish" if a.mark_first else "publish_then_mark",
                 resume=not a.no_resume, **SCENARIOS[a.scenario])
    result, trace = simulate(s)
    print(f"scenario={a.scenario} atomic={s.atomic} step_key={s.step_key} dedup={s.consumer_dedup} "
          f"relay={s.relay_order} resume={s.resume}")
    print(f"refunds={result['refunds']} journal_steps={result['journal_steps']} outbox_rows={result['outbox_rows']} "
          f"deliveries={result['deliveries']} ledger_entries={result['ledger_entries']}")
    print(f"invariants: duplicate_refunds={result['duplicate_refunds']} lost_events={result['lost_events']} "
          f"duplicate_postings={result['duplicate_postings']}")
    if a.trace:
        print("\n".join("  " + t for t in trace))


if __name__ == "__main__":
    main()
