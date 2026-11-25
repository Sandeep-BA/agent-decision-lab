"""Author: Sandeep Belgavi. The model must reproduce every documented redis.io example."""
import unittest
from example import SetModel, documented_examples, surprises


class DocumentedExamples(unittest.TestCase):
    def test_sexpire_page(self):
        self.assertEqual(documented_examples(), {"sexpire_no_key": [-2, -2], "sexpire_10": [1, 1, -2],
                                                 "sexpire_20_nx": [0], "sexpire_20_gt": [1], "sttl": [20, 10]})

    def test_sttl_page(self):
        s = SetModel()
        self.assertEqual(s.sttl("member1", "member2"), [-2, -2])
        s.sadd("member1", "member2")
        self.assertEqual(s.sexpire(300, "member1", "member3"), [1, -2])
        self.assertEqual(s.sttl("member1", "member2", "member3"), [300, -1, -2])

    def test_spersist_page(self):
        s = SetModel()
        s.sadd("member1", "member2")
        self.assertEqual(s.sexpire(300, "member1", "member2"), [1, 1])
        self.assertEqual(s.spersist("member2"), [1])
        self.assertEqual(s.sttl("member1", "member2"), [300, -1])
        self.assertEqual(s.spersist("member2", "member3"), [-1, -2])

    def test_saddex_page(self):
        s = SetModel()
        self.assertEqual(s.saddex("member1", "member2", ex=300), 1)
        self.assertEqual(s.sttl("member1", "member2"), [300, 300])
        self.assertEqual(s.saddex("member2", "member3", ex=60, mnx=True), 0)
        self.assertEqual(s.saddex("member1", "member3", keepttl=True), 1)
        self.assertEqual(s.sttl("member1", "member2", "member3"), [300, 300, -1])
        self.assertEqual(s.saddex("member1"), 1)
        self.assertEqual(s.sttl("member1"), [-1])
        self.assertEqual(s.saddex("member2", "member4", mxx=True), 0)
        with self.assertRaises(ValueError):
            s.saddex("member1", ex=10, keepttl=True)


class Semantics(unittest.TestCase):
    def test_zero_ttl_removes_member_and_empty_key(self):
        s = SetModel()
        s.sadd("a")
        self.assertEqual(s.sexpire(0, "a"), [2])
        self.assertFalse(s.key_exists())

    def test_expired_member_is_missing_but_may_be_counted(self):
        s = SetModel()
        s.sadd("a", "b")
        s.sexpire(5, "a")
        s.advance(5)
        self.assertEqual(s.sismember("a"), 0)
        self.assertEqual(s.scard_upper_bound(), 2)
        self.assertEqual(s.live_count(), 1)
        self.assertEqual(s.sttl("a"), [-2])

    def test_surprises(self):
        self.assertEqual(surprises(), {"ttl_after_sadd": 900, "ttl_after_plain_saddex": -1,
                                       "gt_on_persistent": [0], "lt_on_persistent": [1],
                                       "member_after_61s": 0, "key_exists_after_61s": False})

    def test_srem_clears_ttl(self):
        s = SetModel()
        s.saddex("a", ex=50)
        self.assertEqual(s.srem("a"), 1)
        s.sadd("a")
        self.assertEqual(s.sttl("a"), [-1])


if __name__ == "__main__":
    unittest.main()
