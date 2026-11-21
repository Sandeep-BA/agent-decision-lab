# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README. Runs real child processes.
import unittest
from run_matrix import BIG, SIZE, matrix, stdout_flush_at_exit


class ExitStatusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {(r['mode'], r['budget']): r for r in matrix()}

    def seen(self, mode, budget):
        r = self.rows[(mode, budget)]
        return r['exit'], r['marker'], r['summary_valid']

    def test_all_modes_succeed_with_space(self):
        for mode in ('swallow', 'marker_first', 'checked'):
            self.assertEqual(self.seen(mode, BIG), (0, True, True), mode)

    def test_swallow_reports_success_for_a_broken_file(self):
        self.assertEqual(self.seen('swallow', 4096), (0, True, False))
        self.assertEqual(self.seen('swallow', SIZE - 100), (0, True, False))

    def test_marker_first_leaves_a_marker_when_close_fails(self):
        self.assertEqual(self.seen('marker_first', SIZE - 100), (1, True, False))

    def test_checked_fails_loudly_without_marker(self):
        for budget in (4096, SIZE - 100):
            self.assertEqual(self.seen('checked', budget), (1, False, False))
            self.assertIn('summary not written', self.rows[('checked', budget)]['stderr_last'])

    def test_interpreter_exit_flush_failure_is_120(self):
        self.assertEqual(stdout_flush_at_exit()['exit'], 120)


if __name__ == '__main__':
    unittest.main()
