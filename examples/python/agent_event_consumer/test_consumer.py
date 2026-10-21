"""Tests for the keyed agent consumer. Author: Sandeep Belgavi."""
import unittest
from pathlib import Path

import consumer as c

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "disputes.json"


def fresh(per_window=6, max_attempts=3, effects=None):
    return c.KeyedAgentConsumer(c.FakeModel(per_window), effects or c.EffectStore(), max_attempts=max_attempts)


class NoKeyEffects(c.EffectStore):
    """A write path without effect keys: every call writes a new row."""

    def contains(self, effect_id):
        return False

    def apply_once(self, effect_id, decision):
        self.order.append(effect_id)
        self.applied[f"{effect_id}#{len(self.order)}"] = decision
        return True


class ConsumerTests(unittest.TestCase):
    def setUp(self):
        self.log = c.load_log(FIXTURE)

    def test_effects_follow_offset_order_within_each_key(self):
        result = c.run(self.log, fresh())
        seen = {}
        for effect_id in result["effect_order"]:
            _topic, p, o = effect_id.split("/")
            key = self.log[int(p)][int(o)].key
            seen.setdefault((p, key), []).append(int(o))
        for offsets in seen.values():
            self.assertEqual(offsets, sorted(offsets))

    def test_poison_is_parked_with_the_later_events_of_its_key(self):
        result = c.run(self.log, fresh())
        parked = [(p, o, k) for p, o, k, _why in result["parked"]]
        self.assertEqual(parked, [(1, 2, "acct-e"), (1, 5, "acct-e"), (1, 7, "acct-e")])
        self.assertEqual(result["effects_applied"], 21)

    def test_rate_limit_pauses_and_never_exceeds_the_window(self):
        consumer = fresh(per_window=6)
        result = c.run(self.log, consumer)
        self.assertGreater(result["rate_limited"], 0)
        self.assertGreater(result["partition_pauses"], 0)
        self.assertTrue(all(n <= 6 for n in consumer.model.calls.values()))
        self.assertEqual(result["model_calls"], 24)  # 21 events plus three attempts on the poison event

    def test_higher_limit_finishes_sooner(self):
        slow = c.run(self.log, fresh(per_window=6))["finished_at"]
        fast = c.run(self.log, fresh(per_window=30))["finished_at"]
        self.assertLess(fast, slow)

    def test_redelivery_after_a_crash_applies_nothing_twice(self):
        result = c.run(self.log, fresh(), crash_at=25)
        self.assertGreater(result["redelivered"], 0)
        self.assertEqual(result["effects_applied"], 21)

    def test_without_effect_keys_redelivery_duplicates_effects(self):
        consumer = fresh(effects=NoKeyEffects())
        result = c.run(self.log, consumer, crash_at=25)
        self.assertGreater(result["redelivered"], 0)
        self.assertEqual(len(consumer.effects.order), 21 + result["redelivered"])

    def test_committing_after_every_event_leaves_nothing_to_redeliver(self):
        result = c.run(self.log, fresh(), crash_at=25, commit_every=None)
        self.assertEqual(result["redelivered"], 0)

    def test_retrying_poison_for_ever_blocks_only_its_partition(self):
        consumer = fresh(max_attempts=10_000)
        result = c.run(self.log, consumer, horizon=200)
        self.assertEqual(result["committed"][0], 8)
        self.assertEqual(result["committed"][2], 8)
        self.assertLess(result["committed"][1], 8)

    def test_disallowed_action_is_an_invalid_decision(self):
        consumer = fresh()
        with self.assertRaises(c.InvalidDecision):
            consumer.validate({"action": "delete_account"})


if __name__ == "__main__":
    unittest.main()
