"""Author: Sandeep Belgavi. Expected outcomes for the RFC 6298 estimator, checked by hand."""
import unittest
import rto as R


class RtoTest(unittest.TestCase):
    def test_initial_and_first_sample(self):
        e = R.RtoEstimator(floor=0.0)
        self.assertEqual(e.rto, 1.0)                       # rule 2.1
        e.sample(0.100)
        self.assertAlmostEqual(e.srtt, 0.100)
        self.assertAlmostEqual(e.rttvar, 0.050)
        self.assertAlmostEqual(e.rto, 0.300)               # 0.1 + 4 * 0.05

    def test_rttvar_uses_the_old_srtt(self):
        e = R.RtoEstimator(floor=0.0)
        e.sample(0.100); e.sample(0.500)
        self.assertAlmostEqual(e.rttvar, 0.75 * 0.05 + 0.25 * 0.4)   # |0.1 - 0.5|, not |0.15 - 0.5|
        self.assertAlmostEqual(e.srtt, 0.875 * 0.1 + 0.125 * 0.5)

    def test_the_one_second_floor_hides_a_short_path_spike(self):
        self.assertEqual({x[1] for x in R.trace(1.0)}, {1.0})
        low = [x[1] for x in R.trace(0.2)]
        self.assertEqual((low[7], low[10]), (0.2, 0.7978))

    def test_long_path_spike_lifts_rto_above_the_floor(self):
        t = [x[1] for x in R.trace(1.0, R.SERIES_LONG)]
        self.assertEqual((t[8], t[10], t[-1]), (1.0351, 1.7029, 1.0305))

    def test_backoff_doubles_and_caps(self):
        self.assertEqual(R.run()['backoff_from_initial'], [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 60.0, 60.0])

    def test_karn_discards_ambiguous_samples(self):
        k = R.karn_demo()
        self.assertEqual(k['careful_rto'], 0.6)            # stays backed off
        self.assertLess(k['naive_rto'], 1.25)              # below the true 1.25 s RTT: spurious retransmits
        e = R.RtoEstimator()
        self.assertFalse(e.sample(0.3, retransmitted=True))
        self.assertTrue(e.sample(0.3, retransmitted=True, timestamps=True))

    def test_syn_loss_reinitialises_to_three_seconds(self):
        e = R.RtoEstimator(); e.sample(0.1)
        e.syn_timed_out_then_established()
        self.assertEqual(e.rto, 3.0)


if __name__ == '__main__':
    unittest.main()
