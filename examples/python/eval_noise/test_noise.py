"""Author: Sandeep Belgavi. Tests for the eval noise example: estimates recover known components."""
import unittest

from noise import components, half_width, implied, synthetic


class NoiseTests(unittest.TestCase):
    def test_printed_estimates(self):
        est = [round(v, 3) for v in components(synthetic())]
        self.assertEqual(est, [0.08, 0.075, 0.094])

    def test_estimates_track_the_implied_values_across_seeds(self):
        imp = implied()
        for seed in range(1, 6):
            est = components(synthetic(n=600, seed=seed))
            for e, i in zip(est, imp):
                self.assertAlmostEqual(e, i, delta=0.02)

    def test_a_perfect_grader_has_zero_grader_variance(self):
        task, generation, grader = components(synthetic(flip=0.0))
        self.assertEqual(grader, 0)
        self.assertGreater(generation, 0.09)

    def test_grader_noise_shrinks_the_real_signal(self):
        clean, noisy = implied(flip=0.0), implied(flip=0.2)
        self.assertAlmostEqual(noisy[0] / clean[0], 0.36)
        self.assertAlmostEqual(noisy[1] / clean[1], 0.36)

    def test_half_widths_in_the_article(self):
        cases = {(200, 1, 1): 6.4, (200, 4, 1): 4.9, (200, 1, 4): 6.0, (200, 4, 4): 4.8, (800, 1, 1): 3.2}
        for (n, K, G), want in cases.items():
            self.assertEqual(round(half_width(0.10, 0.08, 0.03, n, K, G), 1), want)
        self.assertEqual(round(half_width(0.10, 0.08, 0.03, 200, 10**9, 10**9), 1), 4.4)


if __name__ == '__main__':
    unittest.main()
