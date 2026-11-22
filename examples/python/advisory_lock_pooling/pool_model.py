# Author: Sandeep Belgavi. A model of PostgreSQL advisory-lock semantics behind a pooler.
# It encodes the documented rules (PostgreSQL 19 docs, section 13.3.5; PgBouncer feature map)
# and is NOT a run against PostgreSQL or PgBouncer. Workers are synthetic; no database needed.
"""Run: python pool_model.py"""
import json


class Server:
    """Backends own session-level advisory locks (re-entrant, counted) and transaction-level ones."""

    def __init__(self, backends):
        self.session = {b: {} for b in backends}   # backend -> {key: count}
        self.xact = {b: set() for b in backends}

    def _held_by_other(self, backend, key):
        return any(b != backend and (key in held or key in self.xact[b]) for b, held in self.session.items())

    def try_lock(self, backend, key):
        if self._held_by_other(backend, key):
            return False
        self.session[backend][key] = self.session[backend].get(key, 0) + 1
        return True

    def unlock(self, backend, key):
        held = self.session[backend]
        if key not in held:
            return False  # PostgreSQL returns false and logs a warning
        held[key] -= 1
        if held[key] == 0:
            del held[key]
        return True

    def try_xact_lock(self, backend, key):
        if self._held_by_other(backend, key):
            return False
        self.xact[backend].add(key)
        return True

    def end_transaction(self, backend):
        self.xact[backend].clear()

    def discard_all(self, backend):  # includes pg_advisory_unlock_all()
        self.session[backend].clear()


class TransactionPool:
    """Each transaction takes the backend that has been idle longest, and returns it at the end."""

    def __init__(self, backends):
        self.idle = list(backends)

    def checkout(self, client):
        return self.idle.pop(0)

    def release(self, backend):
        self.idle.append(backend)


class SessionPool:
    """Each client keeps one backend until it disconnects; DISCARD ALL runs on release."""

    def __init__(self, backends):
        self.idle, self.pinned = list(backends), {}

    def checkout(self, client):
        if client not in self.pinned:
            self.pinned[client] = self.idle.pop(0)
        return self.pinned[client]

    def release(self, backend):
        pass

    def disconnect(self, server, client):
        b = self.pinned.pop(client)
        server.discard_all(b)
        self.idle.append(b)


def run_session_lock(pool_cls):
    server, pool, trace = Server(['S1', 'S2']), pool_cls(['S1', 'S2']), []

    def stmt(client, op, key=42):
        b = pool.checkout(client)
        r = {'try_lock': server.try_lock, 'unlock': server.unlock}[op](b, key) if op != 'work' else None
        server.end_transaction(b)
        pool.release(b)
        trace.append({'client': client, 'op': op, 'backend': b, 'result': r})
        return r

    stmt('tanishka', 'try_lock')   # nightly reindex job takes lock 42
    stmt('tanishka', 'work')
    stmt('jenya', 'try_lock')      # a second copy of the job must be refused
    stmt('tanishka', 'unlock')
    stmt('jenya', 'unlock')
    holders = {b: dict(h) for b, h in server.session.items() if h}
    return {'trace': trace, 'both_believed_they_held': trace[0]['result'] and trace[2]['result'], 'left_held': holders}


def run_xact_lock():
    server, pool, trace = Server(['S1', 'S2']), TransactionPool(['S1', 'S2']), []
    t = pool.checkout('tanishka')                    # BEGIN
    trace.append({'client': 'tanishka', 'op': 'try_xact_lock', 'backend': t, 'result': server.try_xact_lock(t, 42)})
    j = pool.checkout('jenya')
    trace.append({'client': 'jenya', 'op': 'try_xact_lock', 'backend': j, 'result': server.try_xact_lock(j, 42)})
    server.end_transaction(j); pool.release(j)
    server.end_transaction(t); pool.release(t)       # COMMIT releases the lock
    j = pool.checkout('jenya')
    trace.append({'client': 'jenya', 'op': 'try_xact_lock', 'backend': j, 'result': server.try_xact_lock(j, 42)})
    server.end_transaction(j); pool.release(j)
    return {'trace': trace, 'left_held': {b: sorted(x) for b, x in server.xact.items() if x}}


def run():
    return {'transaction_pool_session_lock': run_session_lock(TransactionPool),
            'session_pool_session_lock': run_session_lock(SessionPool),
            'transaction_pool_xact_lock': run_xact_lock()}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
