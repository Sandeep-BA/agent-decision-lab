"""Tests for the reasoning-state passthrough example. Author: Sandeep Belgavi."""
import unittest

from transcript import (ANTHROPIC_RESPONSE, GEMINI_RESPONSE, OPENAI_OUTPUT, Store, check,
                        merge_gemini_text, only_thinking_filter)

CASES = [("anthropic", "claude-family-a", ANTHROPIC_RESPONSE), ("openai", "gpt-family-a", OPENAI_OUTPUT),
         ("gemini", "gemini-family-a", GEMINI_RESPONSE)]


class Passthrough(unittest.TestCase):
    def test_neutral_store_drops_reasoning_state_for_every_provider(self):
        for provider, family, response in CASES:
            store = Store(keep_native=False)
            store.save(provider, family, response)
            self.assertEqual(len(check(provider, response, store.replay(provider, family))), 1, provider)

    def test_store_with_native_payload_round_trips_byte_for_byte(self):
        for provider, family, response in CASES:
            store = Store(keep_native=True)
            store.save(provider, family, response)
            replayed = store.replay(provider, family)
            self.assertEqual(replayed, response, provider)
            self.assertEqual(check(provider, response, replayed), [], provider)

    def test_tool_calls_survive_either_way(self):
        store = Store(keep_native=False)
        store.save("anthropic", "claude-family-a", ANTHROPIC_RESPONSE)
        self.assertEqual(store.turns[-1]["tool_calls"][0]["args"], {"order_id": "O-88213"})

    def test_switching_family_falls_back_to_the_neutral_form(self):
        store = Store(keep_native=True)
        store.save("anthropic", "claude-family-a", ANTHROPIC_RESPONSE)
        replayed = store.replay("anthropic", "claude-family-b")
        self.assertFalse(any(b["type"] in ("thinking", "redacted_thinking") for b in replayed["content"]))

    def test_filtering_on_thinking_type_drops_redacted_blocks(self):
        self.assertEqual(len(check("anthropic", ANTHROPIC_RESPONSE, only_thinking_filter(ANTHROPIC_RESPONSE))), 1)

    def test_merging_gemini_parts_moves_the_signature(self):
        self.assertEqual(len(check("gemini", GEMINI_RESPONSE, merge_gemini_text(GEMINI_RESPONSE))), 1)


if __name__ == "__main__":
    unittest.main()
