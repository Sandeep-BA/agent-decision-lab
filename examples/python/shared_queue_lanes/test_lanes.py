"""Author: Sandeep Belgavi."""
import unittest
from lanes import Item, flood_fixture, simulate


class SharedQueue(unittest.TestCase):
    def setUp(self):
        self.items = flood_fixture(agent_per_tick=2, ticks=20)

    def test_strict_priority_starves_the_human_case(self):
        started, trace = simulate(self.items, 'strict', 20)
        self.assertIsNone(started['CASE-1001'])
        self.assertEqual(sum(1 for _, item, _ in trace if item), 20)

    def test_aging_serves_it_when_age_closes_the_priority_gap(self):
        # At tick 4 the case scores 3+4 and the oldest agent item 5+2; the tie goes to the earlier arrival.
        started, _ = simulate(self.items, 'aging', 20, aging=1)
        self.assertEqual(started['CASE-1001'], 4)

    def test_weighted_lanes_bound_the_wait_without_losing_throughput(self):
        started, trace = simulate(self.items, 'lanes', 20, weights={'human': 1, 'agent': 3})
        self.assertEqual(started['CASE-1001'], 2)
        self.assertEqual(sum(1 for _, item, _ in trace if item), 20)

    def test_idle_ticks_and_invalid_input(self):
        started, trace = simulate([Item('CASE-1002', 'human', 3, 1)], 'strict', 5)
        self.assertEqual(started['CASE-1002'], 3)
        self.assertEqual([t[2] for t in trace[:3]], ['idle'] * 3)
        with self.assertRaises(ValueError):
            simulate(self.items, 'random', 5)
        with self.assertRaises(ValueError):
            simulate(self.items, 'lanes', 5, weights={'human': 0, 'agent': 1})


if __name__ == '__main__':
    unittest.main()
