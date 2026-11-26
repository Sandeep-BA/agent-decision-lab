"""Author: Sandeep Belgavi. Tests for persisting and displaying streamed A2A answers."""
import contextlib
import io
import json
import unittest
from pathlib import Path
from example import client_events, display, main, persisted, stream

ANSWER = "Your order BK-2231 ships Friday."


def run(kind, policy):
    return client_events(stream(kind), policy)


class StreamPersistence(unittest.TestCase):
    def test_per_update_persists_nothing_without_last_chunk(self):
        self.assertEqual(persisted(run("deltas_then_status", "per_update")), "")

    def test_per_update_persists_only_the_last_delta(self):
        self.assertEqual(persisted(run("last_chunk_on_final_delta", "per_update")), "ships Friday.")

    def test_per_update_is_fine_when_server_sends_the_whole_artifact(self):
        self.assertEqual(persisted(run("full_artifact_at_end", "per_update")), ANSWER)

    def test_aggregate_persists_but_duplicates_on_screen(self):
        for kind in ("deltas_then_status", "last_chunk_on_final_delta", "full_artifact_at_end"):
            ev = run(kind, "aggregate")
            self.assertEqual(persisted(ev), ANSWER)
            self.assertEqual(display(ev, "keyed"), ANSWER * 2)

    def test_recommended_persists_once_and_displays_once(self):
        for kind in ("deltas_then_status", "last_chunk_on_final_delta", "full_artifact_at_end"):
            ev = run(kind, "recommended")
            self.assertEqual(persisted(ev), ANSWER)
            self.assertEqual(display(ev, "keyed"), ANSWER)

    def test_naive_append_display_always_duplicates_a_final_event(self):
        self.assertNotEqual(display(run("deltas_then_status", "recommended"), "append"), ANSWER)

    def test_expected_file_matches(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            out = main()
        expected = json.loads(Path(__file__).with_name("expected.json").read_text(encoding="utf-8"))
        self.assertEqual(out, expected)


if __name__ == "__main__":
    unittest.main()
