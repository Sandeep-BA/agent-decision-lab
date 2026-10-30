"""Shared versus isolated state in agent evaluation trials.

Author: Sandeep Belgavi. Companion to "Isolating Agent Evaluation Trials" (aicassindra.com).
Synthetic fixtures only: a SQLite template with one damaged-book order, and a scripted refund agent with a
three-call budget. Nothing calls a model or a network.

The task needs four tool calls: look up the case, create a return, approve it, refund it. With a fresh
database the agent runs out of budget every time. With a shared database the first trial leaves an approved
return behind, so the second and third trials finish the refund and pass: the score is inflated by state,
not by the agent. A start-state fingerprint catches the leak.
"""
import hashlib
import os
import shutil
import sqlite3
import tempfile

BUDGET = 3


def build_template(path):
    con = sqlite3.connect(path)
    con.executescript('''
        CREATE TABLE orders (id TEXT PRIMARY KEY, case_id TEXT, item TEXT, amount_cents INT);
        CREATE TABLE returns (order_id TEXT, status TEXT);
        CREATE TABLE refunds (order_id TEXT, amount_cents INT);
        INSERT INTO orders VALUES ('O-4417', 'CASE-4417', 'Damaged hardcover', 1850);
    ''')
    con.commit()
    con.close()


def fingerprint(path):
    con = sqlite3.connect(path)
    h = hashlib.sha256()
    for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        for row in con.execute('SELECT * FROM "%s" ORDER BY 1' % name):
            h.update(repr((name, row)).encode())
    con.close()
    return h.hexdigest()


def refund_agent(con):
    """Scripted agent. Each tool call costs one unit of a three-call budget."""
    calls = 0
    order_id, amount = con.execute("SELECT id, amount_cents FROM orders WHERE case_id = 'CASE-4417'").fetchone()
    calls += 1                                                     # lookup_case
    if con.execute('SELECT 1 FROM refunds WHERE order_id = ?', (order_id,)).fetchone():
        return 'already refunded', calls
    status = con.execute('SELECT status FROM returns WHERE order_id = ?', (order_id,)).fetchone()
    for step in ('create_return', 'approve_return', 'create_refund'):
        if step == 'create_return' and status:
            continue
        if step == 'approve_return' and status and status[0] == 'approved':
            continue
        if calls >= BUDGET:
            return 'out of budget before %s' % step, calls
        calls += 1
        if step == 'create_return':
            con.execute("INSERT INTO returns VALUES (?, 'requested')", (order_id,))
        elif step == 'approve_return':
            con.execute("UPDATE returns SET status = 'approved' WHERE order_id = ?", (order_id,))
        else:
            con.execute('INSERT INTO refunds VALUES (?, ?)', (order_id, amount))
    con.commit()
    return 'refunded', calls


def grade(path):
    """Pass if exactly one refund of the full amount exists for the order."""
    con = sqlite3.connect(path)
    rows = con.execute("SELECT amount_cents FROM refunds WHERE order_id = 'O-4417'").fetchall()
    con.close()
    return rows == [(1850,)]


def run_trial(path, expected=None):
    if expected is not None and fingerprint(path) != expected:
        return {'result': 'invalid: start state differs from the template', 'passed': None}
    con = sqlite3.connect(path)
    outcome, calls = refund_agent(con)
    con.commit()
    con.close()
    return {'result': outcome, 'calls': calls, 'passed': grade(path)}


def suite(mode, trials=3, check=False):
    work = tempfile.mkdtemp(prefix='trials-')
    template = os.path.join(work, 'template.sqlite')
    build_template(template)
    expected = fingerprint(template)
    shared = os.path.join(work, 'shared.sqlite')
    shutil.copyfile(template, shared)
    results = []
    for n in range(1, trials + 1):
        if mode == 'isolated':
            path = os.path.join(work, 'trial-%d.sqlite' % n)
            shutil.copyfile(template, path)
        else:
            path = shared
        results.append(run_trial(path, expected if check else None))
    unchanged = fingerprint(template) == expected
    shutil.rmtree(work, ignore_errors=True)
    return results, unchanged


def main():
    for mode, check in (('shared', False), ('isolated', False), ('shared', True)):
        results, unchanged = suite(mode, check=check)
        passed = sum(1 for r in results if r['passed'])
        label = mode + (' + fingerprint check' if check else '')
        print('%-28s passed %d/3  %s  template unchanged: %s' % (label, passed, [r['result'] for r in results], unchanged))


if __name__ == '__main__':
    main()
