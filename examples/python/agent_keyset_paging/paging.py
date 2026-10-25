"""Offset versus keyset paging for a slow agent reader on a changing list.

Author: Sandeep Belgavi. Standard library only; synthetic data; no network.

The list holds ids 1..N ordered newest first. Between page requests the agent "thinks" for a fixed
number of seconds; meanwhile new items arrive at the top and items the reader already passed are
closed. The same rules drive the browser lab "Agent paging: offset drift versus keyset cursors" on
aicassindra.com, so the numbers here match the lab defaults.
"""
import base64
import hashlib
import hmac
import json


class ChangingList:
    """Newest-first list of integer ids with timed inserts (at the top) and closes (near the reader)."""

    def __init__(self, items=1000, inserts_per_min=3, deletes_per_min=1):
        self.live = list(range(items, 0, -1))
        self.start = set(self.live)
        self.deleted = set()
        self.next_id = items + 1
        self.insert_gap = 60 / inserts_per_min if inserts_per_min else float('inf')
        self.delete_gap = 60 / deletes_per_min if deletes_per_min else float('inf')
        self.ni = 1
        self.nd = 1
        self.inserted = 0

    def advance(self, t, reader_offset):
        """Apply every insert and close due at or before time t, in time order."""
        events = []
        while self.ni * self.insert_gap <= t + 1e-9:
            events.append((self.ni * self.insert_gap, 'i'))
            self.ni += 1
        while self.nd * self.delete_gap <= t + 1e-9:
            events.append((self.nd * self.delete_gap, 'd'))
            self.nd += 1
        events.sort(key=lambda e: (e[0], e[1]))
        for _, kind in events:
            if kind == 'i':
                self.live.insert(0, self.next_id)
                self.next_id += 1
                self.inserted += 1
            elif self.live:
                pos = max(0, min(len(self.live) - 1, reader_offset - 5))
                self.deleted.add(self.live.pop(pos))

    def stable(self):
        return self.start - self.deleted


def scan(mode, items=1000, page_size=50, think_sec=20, inserts_per_min=3, deletes_per_min=1, max_pages=40):
    """Run one scan and return a result dict with pages, duplicates and missed items."""
    if mode not in ('offset', 'keyset'):
        raise ValueError('mode must be offset or keyset')
    lst = ChangingList(items, inserts_per_min, deletes_per_min)
    seen, dups, returned, pages = set(), 0, 0, 0
    offset, last_id = 0, None
    for k in range(max_pages):
        lst.advance(k * think_sec, offset)
        if mode == 'offset':
            ids = lst.live[offset:offset + page_size]
            offset += page_size
        else:
            ids = [i for i in lst.live if last_id is None or i < last_id][:page_size]
            if ids:
                last_id = ids[-1]
            offset += len(ids)
        pages += 1
        returned += len(ids)
        for i in ids:
            if i in seen:
                dups += 1
            seen.add(i)
        if len(ids) < page_size:
            break
    missed = len([i for i in lst.stable() if i not in seen])
    return {'mode': mode, 'pages': pages, 'returned': returned, 'duplicates': dups,
            'missed': missed, 'inserted': lst.inserted, 'closed': len(lst.deleted)}


# ---- The agent-facing tool: signed opaque cursor, page cap ----

SECRET = b'example-only-secret'   # load from a secret store in real code


def encode_cursor(last_created_at, last_id, secret=SECRET):
    body = json.dumps([last_created_at, last_id]).encode()
    tag = hmac.new(secret, body, hashlib.sha256).digest()[:16]
    return base64.urlsafe_b64encode(tag + body).decode()


def decode_cursor(token, secret=SECRET):
    raw = base64.urlsafe_b64decode(token.encode())
    tag, body = raw[:16], raw[16:]
    if not hmac.compare_digest(tag, hmac.new(secret, body, hashlib.sha256).digest()[:16]):
        raise ValueError('cursor was modified')
    return json.loads(body)


def list_open_tickets(rows, cursor=None, page_size=50, max_page_size=100):
    """Keyset page over rows sorted by (created_at, id) descending. rows: list of dicts."""
    page_size = max(1, min(page_size, max_page_size))
    ordered = sorted(rows, key=lambda r: (r['created_at'], r['id']), reverse=True)
    if cursor:
        after = tuple(decode_cursor(cursor))
        ordered = [r for r in ordered if (r['created_at'], r['id']) < after]
    page = ordered[:page_size]
    nxt = encode_cursor(page[-1]['created_at'], page[-1]['id']) if len(page) == page_size else None
    return {'items': page, 'next_cursor': nxt}


def demo():
    for mode in ('offset', 'keyset'):
        print('defaults           ', scan(mode))
    for mode in ('offset', 'keyset'):
        print('1 insert, 4 closes ', scan(mode, inserts_per_min=1, deletes_per_min=4))


if __name__ == '__main__':
    demo()
