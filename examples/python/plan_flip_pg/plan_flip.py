# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

"""Observing a PostgreSQL prepared statement flip from custom to generic plans on skewed data.

Set PG_DSN and run against a throwaway database. Without it, only the offline parser test runs.
"""
import os
import sys


def plan_kind(explain_lines):
    """Classify EXPLAIN text: a $1 in a filter or index condition is the sign of a generic plan."""
    text = "\n".join(explain_lines)
    return "generic" if "$1" in text else "custom"


SETUP = """
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY, store_id int NOT NULL,
                     placed_at timestamptz NOT NULL, total_cents int NOT NULL, note text);
INSERT INTO orders (store_id, placed_at, total_cents, note)
  SELECT CASE WHEN g % 10 < 7 THEN 1 ELSE 2 + (g % 2000) END,
         now() - (g || ' seconds')::interval, 500 + g % 7000, repeat('x', 60)
  FROM generate_series(1, 800000) g;
CREATE INDEX orders_store_id ON orders(store_id);
CREATE INDEX orders_placed_at ON orders(placed_at);
ANALYZE orders;
"""


def main():
    import psycopg
    dsn = os.environ["PG_DSN"]
    with psycopg.connect(dsn, autocommit=True, prepare_threshold=None) as c:
        c.execute(SETUP)
        c.execute("PREPARE recent_orders(int) AS SELECT id, total_cents FROM orders "
                  "WHERE store_id = $1 ORDER BY placed_at DESC LIMIT 20")
        for i, store in enumerate((7, 8, 9, 10, 11, 20, 21, 22), start=1):
            lines = [r[0] for r in c.execute(f"EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF) EXECUTE recent_orders({store})")]
            ms = next(l for l in lines if "Execution Time" in l)
            print(i, store, plan_kind(lines), ms.strip())
        print(c.execute("SELECT name, generic_plans, custom_plans FROM pg_prepared_statements").fetchall())


if __name__ == "__main__":
    if not os.environ.get("PG_DSN"):
        sys.exit("Set PG_DSN to a disposable PostgreSQL database first.")
    main()
