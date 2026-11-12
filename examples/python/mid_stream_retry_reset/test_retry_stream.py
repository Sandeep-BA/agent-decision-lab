"""Author: Sandeep Belgavi. Expected outcomes for mid-stream retry handling."""
import unittest
from retry_stream import STREAM, accumulate, effect_keys


class RetryStreamTests(unittest.TestCase):
    def test_naive_concatenates_and_double_executes(self):
        r = accumulate(STREAM, "naive")
        self.assertIn("Refunding the damChecking", r["text"])
        self.assertEqual(len(r["executed"]), 2)

    def test_reset_fixes_text_but_not_eager_tools(self):
        r = accumulate(STREAM, "reset")
        self.assertEqual(r["text"], "Checking order ORD-7781. The book arrived damaged, so I have started a full refund.")
        self.assertEqual([c["id"] for c in r["calls"]], ["c7"])
        self.assertEqual(len(r["executed"]), 2)

    def test_execute_only_after_finish(self):
        r = accumulate(STREAM, "reset-late-exec")
        self.assertEqual([(c["id"], c["attempt"]) for c in r["executed"]], [("c7", 2)])

    def test_provider_ids_differ_but_content_key_matches(self):
        r = accumulate(STREAM, "reset")
        self.assertEqual({c["id"] for c in r["executed"]}, {"c1", "c7"})
        self.assertEqual(len(effect_keys(r["executed"])), 1)

    def test_ui_saw_a_reset_marker(self):
        self.assertIn("[reset]", accumulate(STREAM, "reset")["shown"])
        self.assertNotIn("[reset]", accumulate(STREAM, "naive")["shown"])


if __name__ == "__main__":
    unittest.main()
