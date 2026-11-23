"""Author: Sandeep Belgavi. Expected outcomes for the routing simulation (simulated, not measured)."""
import unittest
import routing as R


class RoutingSimulationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {r['router']: r for r in R.run()}

    def test_every_request_completes_under_every_router(self):
        self.assertEqual({r['completed'] for r in self.rows.values()}, {1200})

    def test_default_run_matches_the_article(self):
        got = {k: (v['short_p50_s'], v['short_p99_s']) for k, v in self.rows.items()}
        self.assertEqual(got, {'round_robin': (3.23, 41.16), 'least_requests': (2.89, 16.81),
                               'p2c_requests': (2.9, 20.35), 'least_kv': (3.01, 4.73)})

    def test_short_request_tail_ordering_holds_for_three_seeds(self):
        for seed in (3, 11, 29):
            rows = {r['router']: r['short_p99_s'] for r in R.run(seed=seed)}
            self.assertLess(rows['least_kv'], rows['least_requests'], seed)
            self.assertLess(rows['least_requests'], rows['round_robin'], seed)

    def test_the_tail_is_queueing_not_decoding(self):
        r = self.rows['round_robin']
        self.assertGreater(r['short_queue_p99_s'], 0.9 * r['short_p99_s'])

    def test_unknown_router_is_rejected(self):
        with self.assertRaises(ValueError):
            R.simulate(R.make_requests(1, 5, 1.0), 'random')


if __name__ == '__main__':
    unittest.main()
