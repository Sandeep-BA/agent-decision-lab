"""Tests for the hold-and-confirm companion; they check the claims in the article. Author: Sandeep Belgavi."""
import os
import sqlite3
import tempfile
import time
import unittest

import holdconfirm as hc


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


class Designs(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def db(self, name):
        return os.path.join(self.dir, name + '.db')

    def test_long_transaction_makes_checkout_wait_for_the_model(self):
        r = hc.race(self.db('long'), 'long', think=1.0, start_checkout_after=0.2)
        self.assertEqual((r['agent'], r['checkout']), ('swapped', 'sold_out'))
        self.assertGreater(r['checkout_wait_s'], 0.6)

    def test_hold_lets_checkout_finish_at_once(self):
        r = hc.race(self.db('hold'), 'hold', think=1.0, start_checkout_after=0.2)
        self.assertEqual((r['agent'], r['checkout']), ('confirmed', 'sold_out'))
        self.assertLess(r['checkout_wait_s'], 0.2)

    def test_expired_hold_returns_the_copy_and_confirm_fails(self):
        path, clock = self.db('expiry'), Clock()
        hc.setup(path)
        h = hc.hold(path, 'CASE-5120', ttl=600, now=clock)
        clock.t += 601
        self.assertEqual(hc.sweep(path, now=clock), 1)
        self.assertEqual(hc.confirm(path, h, now=clock), 'hold_expired')
        self.assertEqual(hc.checkout(path)[0], 'sold')

    def test_confirm_before_expiry_wins_and_sweep_does_nothing(self):
        path, clock = self.db('confirm'), Clock()
        hc.setup(path)
        h = hc.hold(path, 'CASE-5120', ttl=600, now=clock)
        self.assertEqual(hc.confirm(path, h, now=clock), 'confirmed')
        clock.t += 601
        hc.sweep(path, now=clock)
        self.assertEqual(hc.checkout(path)[0], 'sold_out')

    def test_no_copy_means_no_hold(self):
        path = self.db('none')
        hc.setup(path, copies=0)
        self.assertIsNone(hc.hold(path, 'CASE-5121', ttl=60))

    def test_one_live_hold_per_case(self):
        path = self.db('unique')
        hc.setup(path, copies=2)
        hc.hold(path, 'CASE-5120', ttl=60)
        with self.assertRaises(sqlite3.IntegrityError):
            hc.hold(path, 'CASE-5120', ttl=60)


if __name__ == '__main__':
    unittest.main()
