# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import unittest
from alignment import (GENERATED, PROMPTS, check_comparable, finished_mask, per_row_prompt_slice,
                       processed, sequence_logprob, sequences, transition_scores)


class AlignmentTest(unittest.TestCase):
    def setUp(self):
        self.seqs, self.scores = sequences(), processed(1.0)

    def test_generated_positions_are_the_last_steps(self):
        ts = transition_scores(self.seqs, self.scores)
        self.assertEqual([len(r) for r in ts], [5, 5])

    def test_mask_stops_after_first_eos(self):
        self.assertEqual(finished_mask(GENERATED)[0], [True, True, True, False, False])
        self.assertEqual(finished_mask(GENERATED)[1], [True] * 5)

    def test_unmasked_pad_steps_change_finished_row_only(self):
        naive = sequence_logprob(self.seqs, self.scores, GENERATED, masked=False)
        masked = sequence_logprob(self.seqs, self.scores, GENERATED, masked=True)
        self.assertAlmostEqual(naive[0], -3.5509, places=4)
        self.assertAlmostEqual(masked[0], -1.7011, places=4)
        self.assertAlmostEqual(naive[1], masked[1])

    def test_per_row_prompt_slice_misaligns_left_padding(self):
        self.assertEqual([len(x) for x in per_row_prompt_slice(self.seqs, PROMPTS)], [6, 5])

    def test_processed_scores_depend_on_temperature(self):
        hot = sequence_logprob(self.seqs, processed(0.7), GENERATED)[1]
        self.assertAlmostEqual(hot, -1.6104, places=4)

    def test_incomparable_traces_are_refused(self):
        a = {'tokenizer_sha256': 'aa11', 'score_kind': 'processed', 'temperature': 1.0, 'steps': 5, 'scores': self.scores}
        self.assertEqual(check_comparable(a, dict(a)), [])
        self.assertEqual(len(check_comparable(a, {**a, 'tokenizer_sha256': 'bb22', 'temperature': 0.7})), 2)
        self.assertIn('scores length does not match generated steps', check_comparable(a, {**a, 'steps': 4}))


if __name__ == '__main__':
    unittest.main()
