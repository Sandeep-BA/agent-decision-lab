# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import unittest
from shadow import cutover_plan, embed_trigrams, embed_words, evaluate


class ShadowTest(unittest.TestCase):
    def setUp(self):
        self.r = evaluate()

    def test_labelled_hits_at_3(self):
        self.assertEqual((self.r['clean']['old_hits'], self.r['clean']['new_hits']), (7, 8))
        self.assertEqual((self.r['typo']['old_hits'], self.r['typo']['new_hits']), (4, 7))

    def test_overlap_is_low_even_where_the_new_index_is_better(self):
        self.assertEqual((self.r['clean']['mean_overlap_at_k'], self.r['typo']['mean_overlap_at_k']), (0.42, 0.25))

    def test_mixing_vectors_from_two_models_breaks_retrieval(self):
        self.assertEqual((self.r['clean']['mixed_hits'], self.r['typo']['mixed_hits']), (2, 0))

    def test_plan_requires_no_class_to_lose_hits(self):
        worse = {'a': {'old_hits': 5, 'new_hits': 4}, 'b': {'old_hits': 3, 'new_hits': 6}}
        self.assertEqual(cutover_plan(worse), {'a': 'old', 'b': 'new'})

    def test_vectors_are_unit_length_and_same_size(self):
        for f in (embed_words, embed_trigrams):
            v = f('return a book')
            self.assertEqual(len(v), 64)
            self.assertAlmostEqual(sum(x * x for x in v), 1.0)


if __name__ == '__main__':
    unittest.main()
