"""Offline tests for the truncation probe; they never call a server. Author: Sandeep Belgavi."""
import json
import pathlib
import unittest

from probe import FILLER, HEAD, TAIL, FakeEmbedServer, probe

HERE = pathlib.Path(__file__).resolve().parent


class Probe(unittest.TestCase):
    def test_truncating_server_hides_the_tail(self):
        out = probe(FakeEmbedServer(limit=256), 256)
        self.assertTrue(out["rows"]["head+filler"]["at_limit"])
        self.assertTrue(out["rows"]["head+filler+tail"]["at_limit"])
        self.assertFalse(out["rows"]["tail"]["at_limit"])
        self.assertFalse(out["tail_changes_vector"])
        self.assertGreater(out["query_vs_tail_chunk"], out["query_vs_long_chunk"])

    def test_large_limit_reads_the_tail(self):
        out = probe(FakeEmbedServer(limit=5000), 5000)
        self.assertTrue(out["tail_changes_vector"])
        self.assertFalse(out["rows"]["head+filler+tail"]["at_limit"])

    def test_strict_mode_fails_loudly(self):
        self.assertIn("exceeds", probe(FakeEmbedServer(limit=256), 256)["truncate_false"])
        self.assertEqual(probe(FakeEmbedServer(limit=5000), 5000)["truncate_false"], "accepted")

    def test_fixture_texts_are_long_enough(self):
        self.assertGreater(len((HEAD + FILLER).split()), 256)
        self.assertLess(len(TAIL.split()), 256)

    def test_expected_offline_output(self):
        want = json.loads((HERE / "expected_offline_output.json").read_text(encoding="utf-8"))
        self.assertEqual({"mode": "offline fake", **probe(FakeEmbedServer(256), 256)}, want)


if __name__ == "__main__":
    unittest.main()
