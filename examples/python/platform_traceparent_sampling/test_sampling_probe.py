"""Tests against the real OpenTelemetry SDK. Author: Sandeep Belgavi."""
import unittest
from sampling_probe import CALLER, PLATFORM_SAMPLED, PLATFORM_UNSAMPLED, handle


class SamplingTest(unittest.TestCase):
    def test_continuing_an_unsampled_parent_exports_nothing(self):
        r = handle({"traceparent": PLATFORM_UNSAMPLED}, "continue")
        self.assertEqual((r["exported"], r["server_recording"]), (0, False))

    def test_continuing_a_sampled_parent_keeps_its_trace_id(self):
        r = handle({"traceparent": PLATFORM_SAMPLED}, "continue")
        self.assertEqual(r["exported"], 3)
        self.assertEqual(r["trace_id"], PLATFORM_SAMPLED.split("-")[1])

    def test_ignore_starts_a_new_sampled_root(self):
        r = handle({"traceparent": PLATFORM_UNSAMPLED}, "ignore")
        self.assertEqual(r["exported"], 3)
        self.assertNotEqual(r["trace_id"], PLATFORM_UNSAMPLED.split("-")[1])

    def test_link_keeps_the_platform_context_without_inheriting_its_decision(self):
        r = handle({"traceparent": PLATFORM_UNSAMPLED}, "link")
        self.assertEqual((r["exported"], r["links"]), (3, 1))

    def test_dedicated_header_continues_the_caller(self):
        r = handle({"traceparent": PLATFORM_UNSAMPLED, "x-caller-traceparent": CALLER}, "dedicated")
        self.assertEqual(r["trace_id"], CALLER.split("-")[1])
        self.assertEqual(r["exported"], 3)


if __name__ == "__main__":
    unittest.main()
