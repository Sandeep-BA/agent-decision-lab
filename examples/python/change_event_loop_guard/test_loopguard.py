"""Tests for loopguard.py. Author: Sandeep Belgavi."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loopguard as lg


def run(name):
    agents, guards = lg.SCENARIOS[name]
    return lg.run(lg.PRODUCTS, lg.EDITS, agents, guards)


class LoopGuardTest(unittest.TestCase):
    def test_drifting_agent_without_guards_loops_until_budget(self):
        _, r = run('drifting_agent_no_guards')
        self.assertTrue(r.budget_hit)
        self.assertEqual(r.calls, 500)

    def test_origin_filter_stops_self_echo(self):
        _, r = run('drifting_agent_origin_filter')
        self.assertFalse(r.budget_hit)
        self.assertEqual(r.calls, 2)            # one call per human edit
        self.assertEqual(r.echoes_ignored, 2)

    def test_origin_filter_alone_does_not_stop_two_agents(self):
        _, r = run('two_agents_origin_filter_only')
        self.assertTrue(r.budget_hit)

    def test_noop_suppression_settles_stable_agents(self):
        store, r = run('two_stable_agents_noop_suppression')
        self.assertFalse(r.budget_hit)
        self.assertGreater(r.noop_skipped, 0)
        self.assertIn('catalogue', store['BK-4001']['tags'])

    def test_hop_limit_is_a_counted_backstop(self):
        _, r = run('two_agents_hop_limit_backstop')
        self.assertFalse(r.budget_hit)
        self.assertEqual(r.max_hop, 4)
        self.assertGreater(r.hop_stops, 0)

    def test_breaking_the_data_cycle_settles_even_with_a_drifting_agent(self):
        _, r = run('cycle_broken_in_the_data')
        self.assertFalse(r.budget_hit)
        self.assertEqual(r.hop_stops, 0)

    def test_events_carry_causation_and_hop(self):
        _, r = run('two_stable_agents_noop_suppression')
        for causation, agent, _product, _field, hop in r.log:
            self.assertIsNotNone(causation)
            self.assertGreaterEqual(hop, 1)


if __name__ == '__main__':
    unittest.main()
