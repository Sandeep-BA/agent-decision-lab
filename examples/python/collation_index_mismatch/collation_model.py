"""Author: Sandeep Belgavi. What a B-tree does when the comparison function changes under it.
Two illustrative collations, NOT glibc's real tables: OLD ignores '-' and ' ' at the first
level (then breaks ties on the full string); NEW compares the characters as written.
The PostgreSQL wiki's own test pair, '1-1' and '11', sorts differently under the two."""
import bisect
from functools import cmp_to_key

IGNORED = {"-", " "}


def old_key(s):
    return ("".join(ch for ch in s if ch not in IGNORED), s)


def new_key(s):
    return (s,)


def build_index(keys, key=old_key):
    """A sorted list stands in for the leaf level of a B-tree built under `key`."""
    return sorted(keys, key=key)


def search(index, value, key=new_key):
    """Binary search as an index scan would do it, with the comparator of the running system."""
    keys = [key(k) for k in index]
    i = bisect.bisect_left(keys, key(value))
    return i < len(index) and index[i] == value, i


def order_violations(index, key=new_key):
    """Adjacent pairs out of order under `key`; the kind of invariant amcheck's bt_index_check verifies."""
    return [(a, b) for a, b in zip(index, index[1:]) if key(a) > key(b)]


def insert_unique(index, value, key=new_key):
    """Uniqueness check by looking at the insertion neighbourhood under the running comparator."""
    found, i = search(index, value, key)
    if found:
        return False
    index.insert(i, value)
    return True


SHELF = ["11", "1-1", "1-2", "12", "1 3", "13", "2-1", "21", "A-10", "A10", "A-2", "A2"]

if __name__ == "__main__":
    idx = build_index(SHELF)
    print("index built under OLD:", idx)
    print("sorted under NEW     :", sorted(SHELF, key=new_key))
    for v in SHELF:
        print(f"{v!r:8} found={search(idx, v)[0]}")
    print("violations:", order_violations(idx))
    copy = list(idx)
    print("insert duplicate '1-2' accepted:", insert_unique(copy, "1-2"), copy.count("1-2"))
