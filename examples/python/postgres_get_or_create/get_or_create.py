"""Get-or-create on PostgreSQL that returns an id in every interleaving. Author: Sandeep Belgavi.

Requires PostgreSQL and psycopg 3 for the concurrent probe (set PG_DSN). The functions take any
DB-API style connection in autocommit mode with %(name)s parameters.
"""
import os
import threading
import time

DO_NOTHING = "INSERT INTO tags(name) VALUES (%(n)s) ON CONFLICT (name) DO NOTHING RETURNING id"
CTE_UNION = ("WITH ins AS (INSERT INTO tags(name) VALUES (%(n)s) ON CONFLICT (name) DO NOTHING RETURNING id) "
             "SELECT id FROM ins UNION ALL SELECT id FROM tags WHERE name = %(n)s LIMIT 1")
DO_UPDATE = "INSERT INTO tags(name) VALUES (%(n)s) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id"
SELECT = "SELECT id FROM tags WHERE name = %(n)s"


def get_or_create(conn, name, attempts=3):
    """Insert-or-skip, then look up in a NEW statement. Under READ COMMITTED each statement takes a
    fresh snapshot, so the lookup sees a row a concurrent transaction committed while we waited.
    The loop covers the rare case where that row was deleted between the two statements."""
    for _ in range(attempts):
        row = conn.execute(DO_NOTHING, {'n': name}).fetchone()
        if row:
            return row[0], 'inserted'
        row = conn.execute(SELECT, {'n': name}).fetchone()
        if row:
            return row[0], 'existing'
    raise RuntimeError(f'could not get or create {name!r} after {attempts} attempts')


def reset(conn):
    conn.execute('DROP TABLE IF EXISTS tags')
    conn.execute('CREATE TABLE tags(id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, name text NOT NULL UNIQUE)')
    conn.execute("INSERT INTO tags(name) VALUES ('poetry')")


def concurrent(connect, statement, key='fantasy'):
    """Another transaction inserts `key` and holds it uncommitted; run `statement` (SQL text or the
    get_or_create function) on a second connection, then commit the first one."""
    other = connect(autocommit=False)
    other.execute('INSERT INTO tags(name) VALUES (%(n)s)', {'n': key})
    me = connect(autocommit=True)
    result = {}

    def run():
        if callable(statement):
            result['value'] = statement(me, key)
        else:
            result['value'] = me.execute(statement, {'n': key}).fetchall()
    th = threading.Thread(target=run)
    th.start()
    time.sleep(0.5)
    result['blocked'] = th.is_alive()
    other.commit()
    th.join(10)
    other.close()
    me.close()
    return result


def pg_connect_factory(dsn):
    import psycopg

    def connect(autocommit=True):
        return psycopg.connect(dsn, autocommit=autocommit)
    return connect


if __name__ == '__main__':
    dsn = os.environ.get('PG_DSN')
    if not dsn:
        raise SystemExit('Set PG_DSN, for example host=127.0.0.1 port=5432 user=postgres dbname=scratch')
    connect = pg_connect_factory(dsn)
    for label, stmt in [('DO NOTHING RETURNING', DO_NOTHING), ('CTE with UNION ALL', CTE_UNION),
                        ('DO UPDATE RETURNING', DO_UPDATE), ('get_or_create()', get_or_create)]:
        admin = connect()
        reset(admin)
        admin.close()
        print(label, concurrent(connect, stmt))
