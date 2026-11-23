"""Tests for the EnvironmentScope lock model. Author: Sandeep Belgavi."""
import unittest

import scope_sim as S


def waits(r):
    return {c['id']: c['wait'] for c in r['calls']}


class ScopeTest(unittest.TestCase):
    def test_shared_makes_every_session_wait_behind_cold_starts(self):
        self.assertEqual(waits(S.simulate(S.CALLS, 'SHARED')), {'c1': 0, 'c2': 75, 'c3': 150, 'c4': 146, 'c5': 221})

    def test_session_scope_only_serializes_one_session(self):
        r = S.simulate(S.CALLS, 'SESSION')
        self.assertEqual(waits(r), {'c1': 0, 'c2': 0, 'c3': 70, 'c4': 0, 'c5': 0})
        self.assertEqual(r['duplicate_creations'], [])

    def test_user_scope_serializes_one_users_sessions(self):
        self.assertEqual(waits(S.simulate(S.CALLS, 'USER'))['c5'], 65)

    def test_scope_narrower_than_the_resource_creates_it_twice(self):
        r = S.simulate(S.CALLS, 'SESSION', resource='user')
        self.assertEqual([d['call'] for d in r['duplicate_creations']], ['c5'])
        self.assertEqual(S.simulate(S.CALLS, 'USER', resource='user')['duplicate_creations'], [])

    def test_close_waits_for_inflight_calls_and_holds_new_ones(self):
        r = S.simulate(S.CALLS + [S.LATE], 'SESSION', close_at={'A': 30})
        self.assertEqual(r['close']['A'], [100, 110])
        late = next(c for c in r['calls'] if c['id'] == 'c6')
        self.assertEqual((late['start'], late['cold']), (110, True))

    def test_locks_do_not_reach_another_process(self):
        r = S.simulate(S.TWO_PROCS, 'SESSION')
        self.assertEqual(r['cross_process_creations'], [{'resource': ['jenya', 's1'], 'procs': ['A', 'B']}])

    def test_scoped_environment_needs_a_session(self):
        with self.assertRaises(ValueError):
            S.simulate([S.Call('x', 'A', 'jenya', None, 0)], 'SESSION')
        self.assertEqual(S.simulate([S.Call('x', 'A', 'jenya', None, 0)], 'SHARED')['calls'][0]['wait'], 0)


if __name__ == '__main__':
    unittest.main()
