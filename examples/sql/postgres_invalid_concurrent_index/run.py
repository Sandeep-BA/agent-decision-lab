"""Author: Sandeep Belgavi. What a failed CREATE INDEX CONCURRENTLY leaves behind on PostgreSQL 18.

Needs DATABASE_URL pointing at a disposable database where tables may be created and dropped.
Records indisvalid / indisready for each failure case, whether the planner uses the leftover index,
and whether the leftover index still grows on INSERT. Exits 1 if an outcome differs from expectation.
"""
import json
import os
import sys
import threading
import time

import psycopg

URL = os.environ.get("DATABASE_URL")
FLAGS = """select c.relname, i.indisvalid, i.indisready, pg_relation_size(c.oid)
           from pg_index i join pg_class c on c.oid = i.indexrelid
           where i.indrelid = 'cic_orders'::regclass and c.relname <> 'cic_orders_pkey' order by 1"""


def flags(conn):
    return {r[0]: {"valid": r[1], "ready": r[2], "bytes": r[3]} for r in conn.execute(FLAGS).fetchall()}


def attempt(conn, sql):
    try:
        conn.execute(sql)
        return "ok"
    except psycopg.Error as e:
        return type(e).__name__


def main():
    if not URL:
        sys.exit("set DATABASE_URL to a disposable PostgreSQL 18 database")
    out, bad = {}, []
    conn = psycopg.connect(URL, autocommit=True)
    out["server_version"] = conn.execute("show server_version").fetchone()[0]
    conn.execute("drop table if exists cic_orders")
    conn.execute("create table cic_orders (id bigint primary key, case_ref text not null, note text)")
    conn.execute("insert into cic_orders select g, 'CASE-' || (g % 50000), 'n' from generate_series(1, 200000) g")

    # 1. A unique build that meets existing duplicates fails while building.
    out["unique_build"] = attempt(conn, "create unique index concurrently cic_ref_key on cic_orders (case_ref)")
    out["after_unique_failure"] = flags(conn)["cic_ref_key"]
    conn.execute("insert into cic_orders select g, 'NEW-' || g, 'n' from generate_series(300000, 349999) g")
    out["unique_leftover_bytes_after_inserts"] = flags(conn)["cic_ref_key"]["bytes"]

    # 2. REINDEX CONCURRENTLY of that invalid index fails the same way and adds a _ccnew index.
    out["reindex"] = attempt(conn, "reindex index concurrently cic_ref_key")
    out["after_reindex_failure"] = sorted(flags(conn))

    # 3. Cancel a build after it marked the index ready, while it waits for an older snapshot.
    holder = psycopg.connect(URL)
    holder.execute("begin isolation level repeatable read")
    holder.execute("select count(*) from cic_orders where id < 10").fetchone()
    builder = psycopg.connect(URL, autocommit=True)
    pid, result = builder.info.backend_pid, {}
    t = threading.Thread(target=lambda: result.update(r=attempt(builder, "create index concurrently cic_ref_idx on cic_orders (case_ref)")))
    t.start()
    phase = None
    for _ in range(600):
        row = conn.execute("select phase from pg_stat_progress_create_index where pid = %s", (pid,)).fetchone()
        phase = row[0] if row else phase
        if phase == "waiting for old snapshots":
            break
        time.sleep(0.1)
    out["phase_when_cancelled"] = phase
    conn.execute("select pg_cancel_backend(%s)", (pid,))
    t.join(30)
    holder.rollback(); holder.close(); builder.close()
    out["cancelled_build"] = result.get("r")
    before = flags(conn)["cic_ref_idx"]
    out["after_cancel"] = {"valid": before["valid"], "ready": before["ready"]}
    conn.execute("insert into cic_orders select g, 'READY-' || g, 'n' from generate_series(3000000, 3049999) g")
    after = flags(conn)["cic_ref_idx"]
    out["ready_leftover_bytes_before_after_50000_inserts"] = [before["bytes"], after["bytes"]]
    out["ready_leftover_grew_on_insert"] = after["bytes"] > before["bytes"]
    plan = " ".join(r[0] for r in conn.execute("explain (costs off) select * from cic_orders where case_ref = 'READY-3000001'").fetchall())
    out["planner_uses_leftover"] = "cic_ref_idx" in plan

    # 3b. The same wait ended by lock_timeout instead of a manual cancel.
    holder = psycopg.connect(URL)
    holder.execute("begin isolation level repeatable read")
    holder.execute("select count(*) from cic_orders where id < 10").fetchone()
    builder = psycopg.connect(URL, autocommit=True)
    builder.execute("set lock_timeout = '2s'")
    out["lock_timeout_build"] = attempt(builder, "create index concurrently cic_note_idx on cic_orders (note)")
    holder.rollback(); holder.close(); builder.close()
    lt = flags(conn)["cic_note_idx"]
    out["after_lock_timeout"] = {"valid": lt["valid"], "ready": lt["ready"]}

    # 4. The listing query from the article, then cleanup with DROP INDEX CONCURRENTLY.
    out["invalid_listing"] = conn.execute("""select indexrelid::regclass::text, indisready from pg_index
        where not indisvalid and indrelid = 'cic_orders'::regclass order by 1""").fetchall()
    for (name, _) in out["invalid_listing"]:
        conn.execute(f"drop index concurrently {name}")
    out["after_cleanup"] = sorted(flags(conn))
    conn.execute("drop table cic_orders")
    conn.close()

    expect = {"unique_build": "UniqueViolation", "after_unique_failure": {"valid": False, "ready": False, "bytes": 0},
              "unique_leftover_bytes_after_inserts": 0, "reindex": "UniqueViolation",
              "after_reindex_failure": ["cic_ref_key", "cic_ref_key_ccnew"], "phase_when_cancelled": "waiting for old snapshots",
              "cancelled_build": "QueryCanceled", "after_cancel": {"valid": False, "ready": True},
              "ready_leftover_grew_on_insert": True, "planner_uses_leftover": False,
              "lock_timeout_build": "LockNotAvailable", "after_lock_timeout": {"valid": False, "ready": True},
              "after_cleanup": []}
    for k, v in expect.items():
        if out[k] != v:
            bad.append(k)
    out["invalid_listing"] = [list(r) for r in out["invalid_listing"]]
    out["mismatches"] = bad
    print(json.dumps(out, indent=2))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
