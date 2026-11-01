"""Author: Sandeep Belgavi. Tests for the stuck-loop detector example."""
import unittest

from detector import LoopDetector, demo, fp, recorded_runs, replay

POLL = frozenset({'job_status'})


class DetectorTests(unittest.TestCase):
    def setUp(self):
        self.runs = recorded_runs()

    def test_each_loop_shape_is_stopped_early(self):
        self.assertEqual(replay(self.runs['exact'], polling=POLL), (3, 'same call and result 3 times'))
        self.assertEqual(replay(self.runs['oscillation'], polling=POLL), (5, 'same call and result 3 times'))
        self.assertEqual(replay(self.runs['paraphrase'], polling=POLL), (3, 'same result 3 times without progress'))

    def test_working_runs_finish(self):
        self.assertEqual(replay(self.runs['healthy'], polling=POLL), (5, 'finished'))
        self.assertEqual(replay(self.runs['polling'], polling=POLL), (8, 'finished'))

    def test_polling_without_the_exemption_is_a_false_alarm(self):
        self.assertEqual(replay(self.runs['polling'])[1], 'same call and result 3 times')

    def test_argument_order_and_volatile_fields_do_not_hide_a_repeat(self):
        self.assertEqual(fp(['t', {'a': 1, 'b': 2}]), fp(['t', {'b': 2, 'a': 1}]))
        self.assertEqual(replay(self.runs['reordered_args'], polling=POLL)[0], 3)

    def test_without_a_detector_only_the_budget_stops_a_loop(self):
        self.assertEqual(replay(self.runs['exact'], repeats=99, no_progress=99), (30, 'step budget'))

    def test_progress_signal_alone_catches_the_paraphrase_loop_later(self):
        steps, reason = replay(self.runs['paraphrase'], repeats=99, no_progress=8, polling=POLL)
        self.assertEqual((steps, reason), (9, 'no progress for 8 steps'))

    def test_progress_resets_the_counter(self):
        det = LoopDetector(repeats=99, no_progress=2)
        self.assertIsNone(det.observe('a', {}, 1, {'s': 1}))
        self.assertIsNone(det.observe('b', {}, 2, {'s': 1}))
        self.assertIsNone(det.observe('c', {}, 3, {'s': 2}))
        self.assertEqual(det.observe('d', {}, 4, {'s': 2}), None)
        self.assertEqual(det.observe('e', {}, 5, {'s': 2}), 'no progress for 2 steps')

    def test_demo_matches_the_readme(self):
        d = dict(demo())
        self.assertEqual(d['budget_only_exact'], (30, 'step budget'))
        self.assertEqual(d['polling_not_exempt'][0], 3)


if __name__ == '__main__':
    unittest.main()
