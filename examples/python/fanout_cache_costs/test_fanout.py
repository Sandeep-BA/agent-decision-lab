# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

import asyncio
import unittest

from fanout import FakeStream, cost, fan_out


class FanoutTest(unittest.TestCase):
    def test_costs_match_the_article_table(self):
        c = cost(40000, 8)
        self.assertEqual(c["no_cache"], 320000)
        self.assertEqual(c["simultaneous"], 400000)
        self.assertEqual(c["warmed"], 78000)

    def test_simultaneous_cache_costs_more_than_no_cache(self):
        c = cost(40000, 8)
        self.assertGreater(c["simultaneous"], c["no_cache"])

    def test_others_start_only_after_the_first_event(self):
        log = []
        agents = [FakeStream("a0", 0.01, 0.03, log), FakeStream("a1", 0.01, 0.03, log), FakeStream("a2", 0.01, 0.03, log)]
        asyncio.run(fan_out(agents))
        self.assertLess(log.index("first-event a0"), log.index("start a1"))
        self.assertLess(log.index("first-event a0"), log.index("start a2"))
        self.assertEqual(sum(1 for line in log if line.startswith("done")), 3)


if __name__ == "__main__":
    unittest.main()
