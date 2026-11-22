# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import unittest
from pool_model import Server, SessionPool, run


class PoolModelTest(unittest.TestCase):
    def setUp(self):
        self.r = run()

    def test_transaction_pooling_lets_two_workers_hold_one_lock(self):
        t = self.r['transaction_pool_session_lock']
        self.assertTrue(t['both_believed_they_held'])
        self.assertEqual([s['backend'] for s in t['trace']], ['S1', 'S2', 'S1', 'S2', 'S1'])

    def test_unlock_on_another_backend_fails_and_the_lock_leaks(self):
        t = self.r['transaction_pool_session_lock']
        self.assertFalse(t['trace'][3]['result'])
        self.assertEqual(t['left_held'], {'S1': {42: 1}})

    def test_session_pooling_keeps_mutual_exclusion(self):
        s = self.r['session_pool_session_lock']
        self.assertFalse(s['both_believed_they_held'])
        self.assertEqual(s['left_held'], {})

    def test_transaction_lock_is_released_at_commit(self):
        x = self.r['transaction_pool_xact_lock']
        self.assertEqual([s['result'] for s in x['trace']], [True, False, True])
        self.assertEqual(x['left_held'], {})

    def test_session_pool_disconnect_discards_locks(self):
        server, pool = Server(['S1']), SessionPool(['S1'])
        b = pool.checkout('dinky')
        self.assertTrue(server.try_lock(b, 7))
        pool.disconnect(server, 'dinky')
        self.assertEqual(server.session['S1'], {})


if __name__ == '__main__':
    unittest.main()
