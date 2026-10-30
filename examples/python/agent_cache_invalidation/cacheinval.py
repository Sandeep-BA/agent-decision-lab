"""Cache-aside invalidation when an agent writes around the application.

Author: Sandeep Belgavi. Companion to "When an Agent Writes Around the Application Cache" (aicassindra.com).
Synthetic fixtures only: the database is a dict with a change log, the cache is a dict, the clock is an
integer passed in by the caller, and the "agent" is a scripted function. Nothing calls a model or a network.

Scenarios: a direct database write stays stale until the TTL; a write through the service is fresh at once;
change-stream invalidation is stale only until the consumer runs; and a slow cache refill after an
invalidation is refused when invalidations leave a versioned tombstone.
"""
from dataclasses import dataclass, field

TTL = 300           # seconds a cached copy lives
TOMBSTONE_TTL = 30  # seconds an invalidation remembers the version it removed


@dataclass
class Database:
    rows: dict = field(default_factory=dict)
    log: list = field(default_factory=list)     # committed changes, in order, like a change stream

    def update(self, book, stock):
        old = self.rows.get(book, {'stock': None, 'version': 0})
        row = {'stock': stock, 'version': old['version'] + 1}
        self.rows[book] = row
        self.log.append((book, dict(row)))
        return row


@dataclass
class Cache:
    versioned: bool = True
    entries: dict = field(default_factory=dict)  # key -> {'row', 'version', 'expires'}

    def get(self, key, now):
        e = self.entries.get(key)
        if e and now < e['expires'] and e['row'] is not None:
            return e['row']
        return None

    def fill(self, key, row, now):
        """Store a row loaded from the database. With versions, never replace a newer entry or tombstone."""
        e = self.entries.get(key)
        if self.versioned and e and now < e['expires'] and e['version'] >= row['version']:
            return False
        self.entries[key] = {'row': row, 'version': row['version'], 'expires': now + TTL}
        return True

    def invalidate(self, key, version, now):
        """Remove the cached row. With versions, leave a short tombstone that remembers `version`."""
        if self.versioned:
            e = self.entries.get(key)
            if e and now < e['expires'] and e['version'] > version:
                return False                     # never remove a newer entry
            self.entries[key] = {'row': None, 'version': version, 'expires': now + TOMBSTONE_TTL}
        else:
            self.entries.pop(key, None)
        return True


@dataclass
class CatalogService:
    db: Database
    cache: Cache

    def read(self, book, now):
        key = 'book:' + book
        row = self.cache.get(key, now)
        if row is not None:
            return row
        row = dict(self.db.rows[book])
        self.cache.fill(key, row, now)
        return row

    def set_stock(self, book, stock, now):
        """The service path: write the row and invalidate the key together."""
        row = self.db.update(book, stock)
        self.cache.invalidate('book:' + book, row['version'], now)
        return row


@dataclass
class ChangeStreamConsumer:
    """Deletes cache keys for every committed change, whoever wrote it."""
    db: Database
    cache: Cache
    position: int = 0

    def poll(self, now):
        handled = 0
        for book, row in self.db.log[self.position:]:
            self.cache.invalidate('book:' + book, row['version'], now)
            handled += 1
        self.position = len(self.db.log)
        return handled


def fresh(versioned=True):
    db = Database()
    db.update('BK-4001', 12)                     # version 1: 12 copies in stock
    return db, Cache(versioned=versioned), None


def scenario_direct_write():
    db, cache, _ = fresh()
    svc = CatalogService(db, cache)
    svc.read('BK-4001', 0)                       # storefront caches version 1
    db.update('BK-4001', 0)                      # agent marks it sold out straight in the database
    return {'t20': svc.read('BK-4001', 20)['stock'], 't299': svc.read('BK-4001', 299)['stock'],
            't300': svc.read('BK-4001', 300)['stock']}


def scenario_service_write():
    db, cache, _ = fresh()
    svc = CatalogService(db, cache)
    svc.read('BK-4001', 0)
    svc.set_stock('BK-4001', 0, 10)              # agent tool calls the service instead
    return {'t20': svc.read('BK-4001', 20)['stock']}


def scenario_change_stream(lag=2):
    db, cache, _ = fresh()
    svc, consumer = CatalogService(db, cache), ChangeStreamConsumer(db, cache, position=len(db.log))
    svc.read('BK-4001', 0)
    db.update('BK-4001', 0)                      # direct write at t=10
    before = svc.read('BK-4001', 10 + lag - 1)['stock']
    consumer.poll(10 + lag)                      # the consumer catches up `lag` seconds later
    after = svc.read('BK-4001', 10 + lag + 1)['stock']
    return {'before_consumer': before, 'after_consumer': after}


def scenario_slow_refill(versioned):
    """A reader misses at t=0 and loads version 1, the service writes version 2 at t=1, then the slow
    reader stores its old row at t=2. Returns the stock the storefront sees at t=3."""
    db, cache, _ = fresh(versioned)
    svc = CatalogService(db, cache)
    old_row = dict(db.rows['BK-4001'])           # slow reader loaded this at t=0
    svc.set_stock('BK-4001', 0, 1)               # version 2 committed and invalidated at t=1
    stored = cache.fill('book:BK-4001', old_row, 2)
    return {'refill_stored': stored, 't3': svc.read('BK-4001', 3)['stock']}


def main():
    rows = [
        ('direct_write', scenario_direct_write()),
        ('service_write', scenario_service_write()),
        ('change_stream_lag_2s', scenario_change_stream(2)),
        ('slow_refill_plain_delete', scenario_slow_refill(False)),
        ('slow_refill_versioned_tombstone', scenario_slow_refill(True)),
    ]
    for name, result in rows:
        print('%-34s %s' % (name, result))


if __name__ == '__main__':
    main()
