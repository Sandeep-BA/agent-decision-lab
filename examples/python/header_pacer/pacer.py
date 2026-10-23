"""Pace an agent fleet from provider rate-limit response headers, and classify refusals.

Author: Sandeep Belgavi.

Instead of hammering into 429s and retrying, read the remaining-token headers the provider returns on
every response and slow down before you are refused. This module models the Anthropic headers; the same
shape applies to OpenAI (x-ratelimit-*) and Gemini. It also separates a retryable refusal from a spend
cap that must not be retried.

Standard library only. No network and no provider call: the headers and errors here are synthetic.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


def _iso(ts: str) -> float:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()


@dataclass
class Pacer:
    """Shared across a fleet: slow down before the provider refuses. Token headroom is the binding limit."""

    floor: float = 0.05                      # start waiting below this fraction of the token limit
    tok_remaining: int | None = None
    tok_limit: int | None = None
    reset_at: str | None = None

    def observe(self, headers: dict) -> None:
        if "anthropic-ratelimit-tokens-remaining" in headers:
            self.tok_remaining = int(headers["anthropic-ratelimit-tokens-remaining"])
        if "anthropic-ratelimit-tokens-limit" in headers:
            self.tok_limit = int(headers["anthropic-ratelimit-tokens-limit"])
        self.reset_at = headers.get("anthropic-ratelimit-tokens-reset", self.reset_at)

    def should_wait(self, now: float) -> float:
        """Seconds to wait before the next call, or 0 to proceed."""
        if self.tok_remaining is None or self.tok_limit is None:
            return 0.0
        if self.tok_remaining <= self.floor * self.tok_limit and self.reset_at:
            return max(0.0, _iso(self.reset_at) - now)
        return 0.0


def classify_error(status: int, body: dict) -> str:
    """Decide what to do with a refusal.

    'retry_after' -> honour the Retry-After header; 'backoff' -> exponential backoff with jitter;
    'stop' -> a spend cap or quota error that needs human action, never a retry.
    """
    if status == 529:
        return "backoff"                     # overloaded_error: transient, worth a backed-off retry
    if status == 429:
        err = body.get("error", {})
        details = err.get("details", {})
        if details.get("error_code") == "enforced_spend_limit_reached":
            return "stop"                    # spend cap: retrying fails until access resumes
        return "retry_after"
    return "backoff"


def effective_input_tokens(usage: dict) -> int:
    """On most Anthropic models only uncached input counts toward ITPM: input + cache_creation."""
    return usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)


def demo():
    p = Pacer()
    now = _iso("2026-10-23T10:00:00Z")
    p.observe({"anthropic-ratelimit-tokens-limit": "2000000",
               "anthropic-ratelimit-tokens-remaining": "80000",
               "anthropic-ratelimit-tokens-reset": "2026-10-23T10:00:12Z"})
    print("wait seconds:", p.should_wait(now))
    print("spend-cap ->", classify_error(429, {"error": {"details": {"error_code": "enforced_spend_limit_reached"}}}))


if __name__ == "__main__":
    demo()
