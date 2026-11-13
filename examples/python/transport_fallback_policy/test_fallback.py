"""Tests for the fallback policy model. Author: Sandeep Belgavi."""
import unittest
from fallback import FLAPPING, PROXY_426, TRANSIENT, run, summary


class FallbackTest(unittest.TestCase):
    def test_transient_outage(self):
        self.assertEqual(summary("per_request", TRANSIENT)["transport"], "WWHHWWWW")
        self.assertEqual(summary("sticky", TRANSIENT)["transport"], "WWHHHHHH")
        self.assertEqual(summary("probe_recover", TRANSIENT)["transport"], "WWHHWWWW")

    def test_sticky_spends_fewest_websocket_attempts(self):
        attempts = {p: summary(p, TRANSIENT)["ws_attempts"] for p in ("per_request", "sticky", "probe_recover")}
        self.assertEqual(attempts, {"per_request": 12, "sticky": 5, "probe_recover": 9})

    def test_426_pins_every_policy_to_http(self):
        for p in ("per_request", "sticky", "probe_recover"):
            r = summary(p, PROXY_426)
            self.assertEqual((r["ws_attempts"], r["http"], r["probes"]), (1, 8, 0))

    def test_flapping_link(self):
        self.assertEqual(summary("sticky", FLAPPING)["retries"], 3)
        self.assertEqual(summary("per_request", FLAPPING)["retries"], 12)
        self.assertEqual(summary("probe_recover", FLAPPING)["probes"], 3)

    def test_failure_after_output_is_not_retried_on_websocket(self):
        s = run("per_request", ["fail_after_output", "ok"])
        self.assertEqual((s.ws_attempts, s.duplicate_output_risk, s.transport), (2, 1, ["http", "ws"]))

    def test_unknown_policy(self):
        with self.assertRaises(ValueError):
            run("magic", TRANSIENT)


if __name__ == "__main__":
    unittest.main()
