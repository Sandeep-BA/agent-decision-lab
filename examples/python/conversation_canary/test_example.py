"""Author: Sandeep Belgavi. Tests for per-conversation canary assignment."""
import unittest
from example import assign, bucket, fnv1a32, new_conversation_share, simulate


class ConversationCanary(unittest.TestCase):
    def test_fnv1a_reference_vectors(self):
        self.assertEqual(fnv1a32(""), 0x811C9DC5)
        self.assertEqual(fnv1a32("a"), 0xE40C292C)

    def test_assignment_is_deterministic(self):
        self.assertEqual(assign("CASE-1", "s", 2500), assign("CASE-1", "s", 2500))

    def test_raising_the_ramp_never_moves_treatment_back(self):
        for i in range(2000):
            cid = f"CASE-{i}"
            seq = [assign(cid, "prompt-v7", r) for r in (0, 100, 1000, 5000, 10000)]
            self.assertEqual(seq, sorted(seq, key=lambda v: v == "treatment"))
            self.assertEqual(seq[0], "control")
            self.assertEqual(seq[-1], "treatment")

    def test_ramp_bounds(self):
        with self.assertRaises(ValueError):
            assign("CASE-1", "s", 10001)
        with self.assertRaises(ValueError):
            simulate("sometimes")

    def test_policies(self):
        request = simulate("request")
        hashed = simulate("hash")
        pinned = simulate("pinned")
        self.assertEqual((request["mixed_conversations"], request["treatment_to_control_switches"]), (338, 198))
        self.assertEqual((hashed["mixed_conversations"], hashed["treatment_to_control_switches"]), (179, 0))
        self.assertEqual(pinned["mixed_conversations"], 0)
        self.assertEqual(pinned["treatment_at_first_turn"], pinned["treatment_at_last_turn"])

    def test_salt_change_reshuffles_open_conversations(self):
        result = simulate("hash", schedule=(2000,), salt_change_at=3)
        self.assertGreater(result["treatment_to_control_switches"], 0)

    def test_share_tracks_ramp(self):
        self.assertAlmostEqual(new_conversation_share(2000), 0.2, delta=0.01)
        self.assertTrue(0 <= bucket("x", "y") < 10000)


if __name__ == "__main__":
    unittest.main()
