"""Replay the synthetic sign-ups against four uniqueness strategies and print what each one stores.

Author: Sandeep Belgavi. Run: python demo.py
"""
import json, pathlib, sqlite3, unicodedata
from canonical import Rejected, load_confusables, naive_keys, skeleton, username_key

HERE = pathlib.Path(__file__).resolve().parent
STRATEGIES = ('raw UNIQUE', 'SQLite NOCASE', 'lower()', 'username_key')


def replay():
    data = json.loads((HERE / 'signups.json').read_text(encoding='utf-8'))
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE raw_users (name TEXT UNIQUE)')
    db.execute('CREATE TABLE nocase_users (name TEXT UNIQUE COLLATE NOCASE)')
    lower_keys, keys = set(), set()
    table = load_confusables()
    skeletons = {}
    for name in data['existing']:
        db.execute('INSERT INTO raw_users VALUES (?)', (name,))
        db.execute('INSERT INTO nocase_users VALUES (?)', (name,))
        lower_keys.add(name.lower())
        keys.add(username_key(name))
        skeletons.setdefault(skeleton(username_key(name), table), name)
    rows = []
    for attempt in data['attempts']:
        name, outcome = attempt['name'], {}
        for strategy, sql in (('raw UNIQUE', 'raw_users'), ('SQLite NOCASE', 'nocase_users')):
            try:
                db.execute('INSERT INTO %s VALUES (?)' % sql, (name,))
                outcome[strategy] = 'stored'
            except sqlite3.IntegrityError:
                outcome[strategy] = 'duplicate'
        low = naive_keys(name)['lower']
        outcome['lower()'] = 'duplicate' if low in lower_keys else 'stored'
        lower_keys.add(low)
        review = ''
        try:
            key = username_key(name)
            outcome['username_key'] = 'duplicate' if key in keys else 'stored'
            if outcome['username_key'] == 'stored':
                skel = skeleton(key, table)
                if skel in skeletons:
                    review = 'looks like ' + skeletons[skel]
                skeletons.setdefault(skel, name)
            keys.add(key)
        except Rejected as error:
            outcome['username_key'] = 'rejected'
            review = str(error)
        rows.append(dict(name=name, expect=attempt['expect'], why=attempt['why'], review=review, **outcome))
    return rows


def wrong(row, strategy):
    """A strategy is wrong when it stores a duplicate or something that should be rejected."""
    got = row[strategy]
    return (row['expect'] in ('same', 'reject') and got == 'stored') or (row['expect'] == 'distinct' and got != 'stored')


def main():
    rows = replay()
    print('Unicode data in this Python: %s' % unicodedata.unidata_version)
    for row in rows:
        shown = row['name'].encode('ascii', 'backslashreplace').decode()
        print('%-24s %-9s %s | %s' % (shown, row['expect'], ' '.join('%s=%s' % (s, row[s]) for s in STRATEGIES), row['review'] or '-'))
    for strategy in STRATEGIES:
        print('%-14s wrong outcomes: %d of %d' % (strategy, sum(wrong(r, strategy) for r in rows), len(rows)))
    print('look-alike flags raised: %d' % sum(r['review'].startswith('looks like') for r in rows))


if __name__ == '__main__':
    main()
