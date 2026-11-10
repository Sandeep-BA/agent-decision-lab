"""Author: Sandeep Belgavi."""
import threading
import unittest
from handler import LockedStock, UnsafeStock, race


class ThreadPoolHazard(unittest.TestCase):
    def test_forced_interleaving_oversells_the_last_copy(self):
        barrier = threading.Barrier(2, timeout=5)
        stock = race(UnsafeStock(1), ['ORD-501', 'ORD-502'], barrier.wait)
        self.assertEqual(sorted(stock.reserved), ['ORD-501', 'ORD-502'])   # two orders, one copy
        self.assertEqual(stock.copies, 0)

    def test_sequential_calls_were_safe(self):
        stock = UnsafeStock(1)
        self.assertTrue(stock.reserve('ORD-501'))
        self.assertFalse(stock.reserve('ORD-502'))

    def test_lock_serializes_check_and_update(self):
        stock = race(LockedStock(5), [f'ORD-{i}' for i in range(40)], lambda: None)
        self.assertEqual(len(stock.reserved), 5)
        self.assertEqual(stock.copies, 0)


if __name__ == '__main__':
    unittest.main()
