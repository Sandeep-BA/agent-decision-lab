"""Tests for the batch submission ledger. Author: Sandeep Belgavi."""
import json
import unittest

import ledger as L


def make(n=12):
    led = L.Ledger()
    for k in range(n):
        led.add(f"ticket-{k:03d}", f"Summarise ticket {k:03d}" + (" INVALID" if k == 7 else ""))
    return led


class LedgerTests(unittest.TestCase):
    def test_results_are_matched_by_custom_id_not_order(self):
        led = make(5)
        provider = L.FakeProvider("anthropic", finish=1.0, seed=3)
        (batch,) = led.plan(10, 10_000)
        bid = led.submit(provider, batch)
        results = provider.results(bid)
        self.assertNotEqual([r["custom_id"] for r in results], [i.custom_id for i in batch])
        led.reconcile(bid, results)
        for item in led.items.values():
            self.assertEqual(item.result, f"summary of {item.prompt[:24]}")

    def test_plan_respects_request_and_byte_limits(self):
        led = make(12)
        self.assertEqual([len(b) for b in led.plan(5, 10_000)], [5, 5, 2])
        line = len(json.dumps({"custom_id": "ticket-000-a0", "body": "Summarise ticket 000"}).encode()) + 1
        self.assertTrue(all(len(b) <= 2 for b in led.plan(100, 2 * line + 5)))

    def test_invalid_request_goes_to_review_and_is_not_resubmitted(self):
        result = L.run("openai")
        self.assertEqual(result["summary"], {"done": 11, "review": 1})
        self.assertEqual(result["applied"], 11)

    def test_partial_expiry_resubmits_only_the_unfinished_requests(self):
        openai = L.run("openai")
        self.assertEqual(openai["rounds"][0], {"succeeded": 2, "retry": 3, "review": 0, "unknown": 0, "already_applied": 0})
        self.assertEqual(openai["attempts"], 15)  # 12 first attempts plus 3 resubmitted

    def test_whole_job_expiry_resubmits_everything_in_it(self):
        gemini = L.run("gemini")
        self.assertEqual(gemini["rounds"][0]["retry"], 5)
        self.assertEqual(gemini["attempts"], 17)
        self.assertEqual(gemini["applied"], 11)

    def test_reconciling_the_same_results_twice_changes_nothing(self):
        led = make(4)
        provider = L.FakeProvider("anthropic", finish=1.0)
        (batch,) = led.plan(10, 10_000)
        bid = led.submit(provider, batch)
        results = provider.results(bid)
        led.reconcile(bid, results)
        before = dict(led.applied)
        again = led.reconcile(bid, results)
        self.assertEqual(led.applied, before)
        self.assertEqual(again["unknown"], 4)

    def test_late_result_of_an_earlier_attempt_is_not_applied(self):
        led = make(2)
        provider = L.FakeProvider("openai", finish=0.0)
        (batch,) = led.plan(10, 10_000)
        first = led.submit(provider, batch)
        led.reconcile(first, provider.results(first))  # everything expired, back to pending
        (batch,) = led.plan(10, 10_000)
        second = led.submit(provider, batch)
        late = [{"custom_id": "ticket-000-a1", "type": "succeeded", "text": "late"}]
        counts = led.reconcile(second, late)
        self.assertEqual(counts["unknown"], 1)
        self.assertNotIn("ticket-000", led.applied)

    def test_custom_ids_match_the_strictest_documented_format(self):
        led = make(3)
        for item in led.items.values():
            item.attempts = 9
            self.assertRegex(item.custom_id, L.CUSTOM_ID)

    def test_repeated_expiry_ends_in_review(self):
        led = make(1)
        provider = L.FakeProvider("anthropic", finish=0.0)
        provider.results = lambda bid: [{"custom_id": c, "type": "expired"} for c, _ in provider.jobs[bid]]
        for _ in range(3):
            for batch in led.plan(10, 10_000):
                bid = led.submit(provider, batch)
                led.reconcile(bid, provider.results(bid))
        self.assertEqual(led.summary(), {"review": 1})


if __name__ == "__main__":
    unittest.main()
