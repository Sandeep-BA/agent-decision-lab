"""Author: Sandeep Belgavi. Batch upserts that repeat a key on PostgreSQL 18.

Needs DATABASE_URL pointing at a disposable database where a table named upsert_stock may be created and
dropped. Runs each statement shape against the same seed rows, records the SQLSTATE or the resulting rows,
and exits 1 if anything differs from expected.json.
"""
import json, os, sys
from pathlib import Path
import psycopg

URL = os.environ.get('DATABASE_URL')
SEED = ["drop table if exists upsert_stock",
        "create table upsert_stock (isbn text primary key, qty int not null, updated_by text not null)",
        "insert into upsert_stock values ('978-0001', 5, 'seed'), ('978-0002', 1, 'seed')"]
BATCH = "('978-0001', 3, 'feed-a'), ('978-0003', 7, 'feed-a'), ('978-0001', 4, 'feed-b')"
CASES = {
    'on_conflict_do_update_repeated_key': f"insert into upsert_stock as s (isbn, qty, updated_by) values {BATCH} on conflict (isbn) do update set qty = s.qty + excluded.qty, updated_by = excluded.updated_by",
    'on_conflict_do_nothing_repeated_key': f"insert into upsert_stock (isbn, qty, updated_by) values {BATCH} on conflict (isbn) do nothing",
    'do_update_repeated_new_key': "insert into upsert_stock as s (isbn, qty, updated_by) values ('978-0009', 1, 'feed-a'), ('978-0009', 2, 'feed-b') on conflict (isbn) do update set qty = s.qty + excluded.qty",
    'do_nothing_repeated_new_key': "insert into upsert_stock (isbn, qty, updated_by) values ('978-0009', 1, 'feed-a'), ('978-0009', 2, 'feed-b') on conflict (isbn) do nothing",
    'merge_repeated_matched_key': f"merge into upsert_stock s using (values {BATCH}) as v(isbn, qty, updated_by) on s.isbn = v.isbn when matched then update set qty = s.qty + v.qty, updated_by = v.updated_by when not matched then insert values (v.isbn, v.qty, v.updated_by)",
    'merge_repeated_new_key': "merge into upsert_stock s using (values ('978-0009', 1, 'feed-a'), ('978-0009', 2, 'feed-b')) as v(isbn, qty, updated_by) on s.isbn = v.isbn when matched then update set qty = s.qty + v.qty when not matched then insert values (v.isbn, v.qty, v.updated_by)",
    'pre_aggregate_sum': f"insert into upsert_stock as s (isbn, qty, updated_by) select isbn, sum(qty), string_agg(updated_by, '+' order by updated_by) from (values {BATCH}) as v(isbn, qty, updated_by) group by isbn on conflict (isbn) do update set qty = s.qty + excluded.qty, updated_by = excluded.updated_by",
    'last_wins_by_sequence': "insert into upsert_stock as s (isbn, qty, updated_by) select distinct on (isbn) isbn, qty, updated_by from (values ('978-0001', 3, 'feed-a', 1), ('978-0003', 7, 'feed-a', 2), ('978-0001', 4, 'feed-b', 3)) as v(isbn, qty, updated_by, seq) order by isbn, seq desc on conflict (isbn) do update set qty = excluded.qty, updated_by = excluded.updated_by",
}


def main():
    if not URL:
        sys.exit('set DATABASE_URL to a disposable PostgreSQL 18 database')
    conn = psycopg.connect(URL, autocommit=True)
    out = {'server_version_major': conn.execute('show server_version').fetchone()[0].split('.')[0], 'cases': {}}
    for name, sql in CASES.items():
        for s in SEED:
            conn.execute(s)
        try:
            conn.execute(sql); outcome = {'sqlstate': None}
        except psycopg.Error as e:
            outcome = {'sqlstate': e.sqlstate, 'message': e.diag.message_primary}
        outcome['rows'] = [list(r) for r in conn.execute('select isbn, qty, updated_by from upsert_stock order by isbn').fetchall()]
        out['cases'][name] = outcome
    conn.execute('drop table upsert_stock')
    print(json.dumps(out, indent=2))
    expected = json.loads((Path(__file__).parent / 'expected.json').read_text(encoding='utf-8'))
    bad = [k for k in expected['cases'] if expected['cases'][k] != out['cases'].get(k)]
    print('mismatches:', len(bad), bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
