"""A model of Redis 8.12 set-member expiration replies. Author: Sandeep Belgavi.

Rules taken from the redis.io command pages for SEXPIRE, STTL, SPERSIST and SADDEX
(read 2026-11-25). Time is a logical integer clock in seconds. This is a teaching model to
reason about replies; it is not Redis, and it was not run against a Redis 8.12 server.
"""
import json

INF = float("inf")


class SetModel:
    def __init__(self):
        self.members = {}  # member -> expire_at (seconds) or None for persistent
        self.now = 0

    def _live(self, m):
        exp = self.members.get(m, "absent")
        if exp == "absent":
            return False
        return exp is None or exp > self.now

    def _purge(self, m):
        if m in self.members and not self._live(m):
            del self.members[m]

    def advance(self, seconds):
        self.now += seconds

    def sadd(self, *ms):
        added = 0
        for m in ms:
            self._purge(m)
            if m not in self.members:
                self.members[m] = None
                added += 1
            # SADD leaves the TTL of an existing member untouched
        return added

    def saddex(self, *ms, ex=None, keepttl=False, mnx=False, mxx=False):
        if ex is not None and keepttl:
            raise ValueError("Only one of EX, PX, EXAT, PXAT or KEEPTTL arguments can be specified")
        if mnx and mxx:
            raise ValueError("MNX and MXX are mutually exclusive")
        for m in ms:
            self._purge(m)
        present = [m in self.members for m in ms]
        if (mnx and any(present)) or (mxx and not all(present)):
            return 0
        for m in ms:
            if keepttl and m in self.members:
                continue
            self.members[m] = None if ex is None else self.now + ex
        return 1

    def sexpire(self, seconds, *ms, cond=None):
        out = []
        for m in ms:
            self._purge(m)
            if m not in self.members:
                out.append(-2)
                continue
            current = self.members[m]
            current_ttl = INF if current is None else current - self.now
            if cond == "NX" and current is not None or cond == "XX" and current is None \
                    or cond == "GT" and not seconds > current_ttl or cond == "LT" and not seconds < current_ttl:
                out.append(0)
                continue
            if seconds <= 0:
                del self.members[m]
                out.append(2)
                continue
            self.members[m] = self.now + seconds
            out.append(1)
        return out

    def sttl(self, *ms):
        out = []
        for m in ms:
            self._purge(m)
            if m not in self.members:
                out.append(-2)
            else:
                exp = self.members[m]
                out.append(-1 if exp is None else exp - self.now)
        return out

    def spersist(self, *ms):
        out = []
        for m in ms:
            self._purge(m)
            if m not in self.members:
                out.append(-2)
            elif self.members[m] is None:
                out.append(-1)
            else:
                self.members[m] = None
                out.append(1)
        return out

    def srem(self, *ms):
        n = 0
        for m in ms:
            if self._live(m):
                n += 1
            self.members.pop(m, None)
        return n

    def sismember(self, m):
        return 1 if self._live(m) else 0

    def scard_upper_bound(self):
        """SCARD may still count expired members that have not been reclaimed yet."""
        return len(self.members)

    def live_count(self):
        return sum(1 for m in self.members if self._live(m))

    def key_exists(self):
        return self.live_count() > 0


def documented_examples():
    s = SetModel()
    r = {"sexpire_no_key": s.sexpire(20, "member1", "member2", cond="NX")}
    s.sadd("member1", "member2")
    r["sexpire_10"] = s.sexpire(10, "member1", "member2", "member3")
    r["sexpire_20_nx"] = s.sexpire(20, "member1", cond="NX")
    r["sexpire_20_gt"] = s.sexpire(20, "member1", cond="GT")
    r["sttl"] = s.sttl("member1", "member2")
    return r


def surprises():
    s = SetModel()
    s.saddex("hold:BK-1001", ex=900)
    s.sadd("hold:BK-1001")                       # SADD keeps the TTL
    after_sadd = s.sttl("hold:BK-1001")[0]
    s.saddex("hold:BK-1001")                     # SADDEX without an option drops it
    after_saddex = s.sttl("hold:BK-1001")[0]
    p = SetModel()
    p.sadd("reader:Jenya")
    gt_on_persistent = p.sexpire(60, "reader:Jenya", cond="GT")
    lt_on_persistent = p.sexpire(60, "reader:Jenya", cond="LT")
    p.advance(61)
    return {"ttl_after_sadd": after_sadd, "ttl_after_plain_saddex": after_saddex,
            "gt_on_persistent": gt_on_persistent, "lt_on_persistent": lt_on_persistent,
            "member_after_61s": p.sismember("reader:Jenya"), "key_exists_after_61s": p.key_exists()}


if __name__ == "__main__":
    print(json.dumps({"documented_examples": documented_examples(), "surprises": surprises()}, indent=2))
