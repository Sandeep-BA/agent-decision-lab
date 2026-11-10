"""Author: Sandeep Belgavi."""
import tempfile
import unittest
from pathlib import Path
from working_set import ANON_HEAVY, CACHE_HEAVY, MIB, analyse, from_directory, parse_stat, read_limit

LIMIT = 1024 * MIB


class WorkingSet(unittest.TestCase):
    def test_cache_heavy_container_looks_full_but_is_mostly_cache(self):
        report = analyse(950 * MIB, LIMIT, parse_stat(CACHE_HEAVY))
        self.assertEqual(report['working_set'], 910 * MIB)
        self.assertEqual(report['working_set_pct'], 88.9)
        self.assertEqual(report['anon_pct'], 29.3)
        self.assertEqual(report['verdict'], 'headroom available')
        report = analyse(1000 * MIB, LIMIT, parse_stat(CACHE_HEAVY))
        self.assertTrue(report['verdict'].startswith('working set high mostly from active page cache'))

    def test_anonymous_memory_near_limit(self):
        report = analyse(1000 * MIB, LIMIT, parse_stat(ANON_HEAVY))
        self.assertTrue(report['verdict'].startswith('anonymous memory near memory.max'))

    def test_inactive_larger_than_usage_clamps_to_zero(self):
        stats = {'anon': 0, 'active_file': 0, 'inactive_file': 10 * MIB}
        self.assertEqual(analyse(5 * MIB, LIMIT, stats)['working_set'], 0)

    def test_unlimited_and_files(self):
        self.assertIsNone(read_limit('max\n'))
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / 'memory.current').write_text(str(950 * MIB))
            (d / 'memory.max').write_text('max\n')
            (d / 'memory.stat').write_text(CACHE_HEAVY)
            self.assertTrue(from_directory(d)['verdict'].startswith('no memory.max'))
        with self.assertRaises(ValueError):
            analyse(1, LIMIT, {'anon': 1})


if __name__ == '__main__':
    unittest.main()
