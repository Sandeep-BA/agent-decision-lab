"""Tests for the header-driven pacer. Standard library unittest only.

Author: Sandeep Belgavi.
"""
import unittest
from datetime import datetime, timezone

from pacer import Pacer, classify_error, effective_input_tokens


def ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


class PacerTests(unittest.TestCase):
    def test_waits_only_when_headroom_is_low(self):
        p = Pacer()
        now = ts("2026-10-23T10:00:00Z")
        p.observe({"anthropic-ratelimit-tokens-limit": "2000000",
                   "anthropic-ratelimit-tokens-remaining": "500000",
                   "anthropic-ratelimit-tokens-reset": "2026-10-23T10:00:30Z"})
        self.assertEqual(p.should_wait(now), 0.0)          # 25% remaining: proceed
        p.observe({"anthropic-ratelimit-tokens-remaining": "80000"})
        self.assertAlmostEqual(p.should_wait(now), 30.0)   # 4% remaining: wait to reset

    def test_waits_before_reaching_zero(self):
        p = Pacer(floor=0.05)
        now = ts("2026-10-23T10:00:00Z")
        waited = False
        for remaining in (300000, 200000, 120000, 90000, 40000):
            p.observe({"anthropic-ratelimit-tokens-limit": "2000000",
                       "anthropic-ratelimit-tokens-remaining": str(remaining),
                       "anthropic-ratelimit-tokens-reset": "2026-10-23T10:00:10Z"})
            if p.should_wait(now) > 0:
                waited = True
                self.assertGreater(remaining, 0)           # it paced before hitting zero
                break
        self.assertTrue(waited)

    def test_spend_cap_must_not_retry(self):
        body = {"error": {"type": "rate_limit_error",
                          "details": {"error_code": "enforced_spend_limit_reached"}}}
        self.assertEqual(classify_error(429, body), "stop")

    def test_ordinary_429_honours_retry_after(self):
        self.assertEqual(classify_error(429, {"error": {}}), "retry_after")

    def test_529_is_a_backed_off_retry(self):
        self.assertEqual(classify_error(529, {"error": {"type": "overloaded_error"}}), "backoff")

    def test_cached_tokens_do_not_count(self):
        usage = {"input_tokens": 1000, "cache_creation_input_tokens": 500,
                 "cache_read_input_tokens": 40000}
        self.assertEqual(effective_input_tokens(usage), 1500)   # cache reads excluded

    def test_no_headers_means_no_wait(self):
        self.assertEqual(Pacer().should_wait(ts("2026-10-23T10:00:00Z")), 0.0)


if __name__ == "__main__":
    unittest.main()
