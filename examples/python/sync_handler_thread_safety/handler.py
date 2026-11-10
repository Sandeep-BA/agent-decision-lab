"""Why a sync request handler that was safe on one event loop can lose updates in a thread pool.

Author: Sandeep Belgavi. Ray 2.60.0 runs sync Serve deployment methods in a thread pool by default
(release notes, 4 November 2026). This file does not import Ray; it reproduces the hazard with
plain threads so the interleaving can be forced and tested deterministically.
"""
import threading


class UnsafeStock:
    """Counts reserved copies with a read-modify-write and no lock."""

    def __init__(self, copies):
        self.copies = copies
        self.reserved = []

    def reserve(self, order_id, between=lambda: None):
        left = self.copies          # read
        between()                   # another thread may run here
        if left <= 0:
            return False
        self.copies = left - 1      # write based on a stale read
        self.reserved.append(order_id)
        return True


class LockedStock(UnsafeStock):
    """Same logic with the whole check-and-update under one lock."""

    def __init__(self, copies):
        super().__init__(copies)
        self._lock = threading.Lock()

    def reserve(self, order_id, between=lambda: None):
        with self._lock:
            return super().reserve(order_id, between)


def race(stock, order_ids, between):
    threads = [threading.Thread(target=stock.reserve, args=(oid, between)) for oid in order_ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
    return stock
