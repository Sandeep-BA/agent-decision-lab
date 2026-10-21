"""A capability gate for agent-generated SQL, built from SQLite's own hooks.

Author: Sandeep Belgavi.

Companion to "Letting an Agent Query an Existing Database" (aicassindra.com, agents).
The agent may read named columns of one table and call a short list of functions. Everything
else is refused inside the SQLite engine by an authorizer callback, the connection is opened
read-only, and a progress handler aborts statements that run past an instruction budget.

The example also keeps a deliberately weaker gate, `view_source_authorizer`, which trusts the
authorizer's fifth argument (the inner-most view responsible for a read) to let a tenant view
read its base table. SQLite reports a common table expression's name in that same argument,
so `WITH refunds_view AS (SELECT * FROM refunds) ...` passes it and reads every tenant's rows.
The safe gate therefore runs against a per-tenant replica that contains no other tenant's data.
Standard library only; no model is called.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent

AGENT_TABLE = "refunds_view"
AGENT_COLUMNS = ("id", "order_id", "amount_cents", "reason", "created_at")
ALLOWED_COLUMNS = {(AGENT_TABLE, c) for c in AGENT_COLUMNS}
ALLOWED_FUNCTIONS = {"count", "sum", "min", "max", "avg", "date", "strftime", "round"}


@dataclass
class Budget:
    """Counts progress-handler callbacks; each callback is `step` virtual machine instructions."""

    max_callbacks: int
    used: int = 0

    def tick(self) -> int:
        self.used += 1
        return 1 if self.used > self.max_callbacks else 0


@dataclass
class GateResult:
    allowed: bool
    rows: list = field(default_factory=list)
    reason: str = ""


def build_fixture(path: Path) -> None:
    """Create the synthetic application database: two tenants, refunds, payments, a tenant-42 view."""
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE refunds (id INTEGER PRIMARY KEY, tenant_id INTEGER NOT NULL, order_id TEXT NOT NULL,
                              amount_cents INTEGER NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE payments (id INTEGER PRIMARY KEY, tenant_id INTEGER NOT NULL, order_id TEXT NOT NULL,
                               card_last4 TEXT NOT NULL);
        INSERT INTO refunds VALUES
          (1, 42, 'O-1001', 1500, 'damaged item', '2026-07-03'),
          (2, 42, 'O-1007', 2000, 'late delivery', '2026-08-14'),
          (3, 42, 'O-1010', 1000, 'duplicate charge', '2026-09-30'),
          (4, 77, 'O-2001', 9900, 'damaged item', '2026-08-01');
        INSERT INTO payments VALUES (1, 42, 'O-1001', '4242'), (2, 77, 'O-2001', '1881');
        CREATE VIEW refunds_view AS
          SELECT id, order_id, amount_cents, reason, created_at FROM refunds WHERE tenant_id = 42;
        """
    )
    conn.commit()
    conn.close()


def build_agent_replica(source: Path, target: Path, tenant_id: int) -> int:
    """Copy one tenant's rows of the agent-facing columns into a database of their own.

    This plays the role that row-level security plays in PostgreSQL: the engine the agent talks
    to holds nothing it must not return, whatever shape the query takes. Returns the row count.
    """
    if target.exists():
        target.unlink()
    src = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
    rows = src.execute(
        f"SELECT {', '.join(AGENT_COLUMNS)} FROM refunds WHERE tenant_id = ? ORDER BY id", (tenant_id,)
    ).fetchall()
    src.close()
    dst = sqlite3.connect(target)
    dst.execute(f"CREATE TABLE {AGENT_TABLE} (id INTEGER PRIMARY KEY, order_id TEXT, amount_cents INTEGER, "
                "reason TEXT, created_at TEXT)")
    dst.executemany(f"INSERT INTO {AGENT_TABLE} VALUES (?, ?, ?, ?, ?)", rows)
    dst.commit()
    dst.close()
    return len(rows)


def strict_authorizer(action, arg1, arg2, db_name, source):
    """Allow SELECT, recursive CTEs (bounded by the progress handler), reads of allowed columns,
    reads of CTE columns (db_name is None) and allowed functions. Deny everything else."""
    if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE):
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ:
        if (arg1, arg2) in ALLOWED_COLUMNS or db_name is None:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION:
        return sqlite3.SQLITE_OK if (arg2 or "").lower() in ALLOWED_FUNCTIONS else sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_DENY


def view_source_authorizer(action, arg1, arg2, db_name, source):
    """UNSAFE on purpose: also allows any read whose inner-most source is named refunds_view.
    A CTE can take that name, so this gate can be bypassed. Kept to demonstrate the bypass."""
    if action == sqlite3.SQLITE_READ and source == AGENT_TABLE:
        return sqlite3.SQLITE_OK
    return strict_authorizer(action, arg1, arg2, db_name, source)


def run(db: Path, sql: str, authorizer=strict_authorizer, max_callbacks: int = 2000, step: int = 1000) -> GateResult:
    """Run one agent statement through the gate. Never raises for refused SQL; reports why."""
    if ";" in sql.strip().rstrip(";"):
        return GateResult(False, reason="more than one statement")
    conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    budget = Budget(max_callbacks)
    conn.set_authorizer(authorizer)
    conn.set_progress_handler(budget.tick, step)
    try:
        rows = conn.execute(sql).fetchmany(1000)
        return GateResult(True, rows=rows)
    except sqlite3.DatabaseError as exc:
        if budget.used > budget.max_callbacks:
            return GateResult(False, reason="interrupted: instruction budget exhausted")
        return GateResult(False, reason=str(exc))
    finally:
        conn.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the synthetic agent statements through both gates.")
    ap.add_argument("--workdir", default=str(HERE / "out"))
    ap.add_argument("--cases", default=str(HERE / "fixtures" / "agent_statements.json"))
    args = ap.parse_args(argv)
    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    app_db, replica = work / "app.db", work / "tenant42.db"
    build_fixture(app_db)
    print(f"replica rows for tenant 42: {build_agent_replica(app_db, replica, 42)}")
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    for name, db, auth in (("view-source gate on the application database", app_db, view_source_authorizer),
                           ("strict gate on the tenant replica", replica, strict_authorizer)):
        print(f"== {name}")
        for case in cases:
            result = run(db, case["sql"], auth)
            verdict = "ALLOWED" if result.allowed else "REFUSED"
            print(f"  {verdict:8} {case['name']}: {result.rows if result.allowed else result.reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
