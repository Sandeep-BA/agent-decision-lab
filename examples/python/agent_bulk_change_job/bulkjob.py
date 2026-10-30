"""A previewed, approved, resumable bulk change instead of a per-row agent tool loop.

Author: Sandeep Belgavi. Companion to "Bulk Changes From an Agent" (aicassindra.com).
Synthetic fixtures only: an in-memory SQLite catalogue of 60 books. The agent's proposal is a fixed
specification; nothing calls a model or a network.

Flow: propose (a declarative spec) -> preview (manifest of (id, version) and its hash) -> approve the hash
-> run in batches, updating a row only if its version still matches, with progress recorded for resume.
"""
import hashlib
import json
import sqlite3

FIELDS = {'publisher', 'format', 'print_year', 'status', 'discount_pct'}
SETTABLE = {'discount_pct', 'tag'}
OPS = {'=', '<', '>', '<=', '>='}


def catalogue():
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE books (id TEXT PRIMARY KEY, publisher TEXT, format TEXT, print_year INT,'
               ' status TEXT, discount_pct INT, tag TEXT, version INT)')
    db.execute('CREATE TABLE job_progress (manifest TEXT, batch INT, PRIMARY KEY (manifest, batch))')
    rows = []
    for i in range(60):
        publisher = 'Harbour Lane Press' if i % 2 == 0 else 'Northfield Books'
        fmt = 'paperback' if i % 3 else 'hardcover'
        year = 2012 + (i % 12)
        discount = 40 if i in (4, 16, 28) else 0
        rows.append(('BK-%d' % (4001 + i), publisher, fmt, year, 'active', discount, '', 1))
    db.executemany('INSERT INTO books VALUES (?,?,?,?,?,?,?,?)', rows)
    return db


def validate(spec):
    for field, op, _ in spec['filter']:
        if field not in FIELDS or op not in OPS:
            raise ValueError('unsupported filter: %s %s' % (field, op))
    for field in spec['set']:
        if field not in SETTABLE:
            raise ValueError('field cannot be set: %s' % field)


def preview(db, spec, sample=3):
    validate(spec)
    where = ' AND '.join('%s %s ?' % (f, op) for f, op, _ in spec['filter'])
    args = [v for _, _, v in spec['filter']]
    rows = db.execute('SELECT id, version FROM books WHERE ' + where + ' ORDER BY id', args).fetchall()
    manifest = json.dumps({'set': spec['set'], 'rows': rows}, sort_keys=True)
    return {'count': len(rows), 'rows': [tuple(r) for r in rows], 'set': dict(spec['set']),
            'sample': [r[0] for r in rows[:sample]], 'hash': hashlib.sha256(manifest.encode()).hexdigest()}


def run(db, plan, approved_hash, batch_size=10, stop_after=None):
    """Apply an approved manifest. Returns (applied, skipped_ids, batches_run)."""
    if approved_hash != plan['hash']:
        raise PermissionError('approval does not match this manifest')
    done_batches = {b for (b,) in db.execute('SELECT batch FROM job_progress WHERE manifest = ?', (plan['hash'],))}
    applied, skipped, ran = 0, [], 0
    sets = ', '.join('%s = ?' % f for f in sorted(plan['set']))
    values = [plan['set'][f] for f in sorted(plan['set'])]
    for n in range(0, len(plan['rows']), batch_size):
        batch = n // batch_size
        if batch in done_batches:
            continue
        if stop_after is not None and ran >= stop_after:
            break
        with db:                                      # one transaction per batch, progress included
            for book_id, version in plan['rows'][n:n + batch_size]:
                cur = db.execute('UPDATE books SET ' + sets + ', version = version + 1 WHERE id = ? AND version = ?',
                                 values + [book_id, version])
                if cur.rowcount:
                    applied += 1
                else:
                    skipped.append(book_id)
            db.execute('INSERT INTO job_progress VALUES (?, ?)', (plan['hash'], batch))
        ran += 1
    return applied, skipped, ran


REQUEST = {'filter': [('publisher', '=', 'Harbour Lane Press'), ('format', '=', 'paperback'),
                      ('print_year', '<', 2019), ('status', '=', 'active')],
           'set': {'discount_pct': 30, 'tag': 'clearance'}}
REVISED = {'filter': REQUEST['filter'] + [('discount_pct', '<=', 30)], 'set': REQUEST['set']}


def main():
    db = catalogue()
    first = preview(db, REQUEST)
    revised = preview(db, REVISED)
    print('first preview   : %d rows, hash %s' % (first['count'], first['hash'][:12]))
    print('revised preview : %d rows, hash %s (books already at 40%% excluded)' % (revised['count'], revised['hash'][:12]))
    changed = [revised['rows'][1][0], revised['rows'][6][0]]
    with db:                                          # a merchandiser reprices two of them meanwhile
        db.executemany('UPDATE books SET discount_pct = 20, version = version + 1 WHERE id = ?', [(c,) for c in changed])
    a1, s1, b1 = run(db, revised, revised['hash'], batch_size=5, stop_after=1)
    print('run, interrupted: applied %d, skipped %s, batches %d' % (a1, s1, b1))
    a2, s2, b2 = run(db, revised, revised['hash'], batch_size=5)
    print('resume          : applied %d, skipped %s, batches %d' % (a2, s2, b2))
    print('per-row loop would have made %d write tool calls; this flow made 2 proposals' % revised['count'])


if __name__ == '__main__':
    main()
