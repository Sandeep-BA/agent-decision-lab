"""Author: Sandeep Belgavi. Tests for the context preflight and drop order."""
import unittest

from preflight import ContextBudgetError, approx_count, budget_for, classify_provider_error, fit, fixture


class PreflightTests(unittest.TestCase):
    def test_demo_clears_three_old_tool_results_and_fits(self):
        out, plan = fit(fixture(), window=8000, max_output=1500)
        self.assertEqual((plan.budget, plan.before, plan.after), (6100, 9438, 5007))
        self.assertEqual(len(plan.actions), 3)
        self.assertTrue(all(a.startswith('cleared tool result') for a in plan.actions))

    def test_recent_turns_system_and_tools_are_never_touched(self):
        out, plan = fit(fixture(), window=4500, max_output=800)
        self.assertTrue(any(a.startswith('removed turn') for a in plan.actions))
        users = [m['content'] for m in out['messages'] if m['role'] == 'user']
        self.assertEqual(users[-2:], ['CASE-6105: customer Dinky asks about order 5', 'CASE-6106: customer Dinky asks about order 6'])
        self.assertEqual(out['system'], fixture()['system'])
        self.assertEqual(out['tools'], fixture()['tools'])
        recent_tools = [m for m in out['messages'] if m['role'] == 'tool' and m['id'] in ('lookup-5', 'lookup-6')]
        self.assertTrue(all(not m.get('cleared') for m in recent_tools))
        self.assertLessEqual(plan.after, plan.budget)

    def test_refuses_instead_of_sending_an_oversized_request(self):
        with self.assertRaises(ContextBudgetError):
            fit(fixture(), window=3000, max_output=1500)

    def test_a_request_that_fits_is_unchanged(self):
        req = fixture()
        out, plan = fit(req, window=200000, max_output=4000)
        self.assertEqual(out, req)
        self.assertEqual(plan.actions, [])

    def test_counter_is_injected(self):
        tool_overhead = lambda r: approx_count(r) + 3000     # e.g. a provider that adds a large tool preamble
        _, plain = fit(fixture(), window=8000, max_output=1500)
        _, heavy = fit(fixture(), window=8000, max_output=1500, count=tool_overhead, keep_turns=1)
        self.assertGreater(len(heavy.actions), len(plain.actions))

    def test_budget_and_error_classification(self):
        self.assertEqual(budget_for(200000, 8000), 182000)
        self.assertIn('context overflow', classify_provider_error(400, {'error': {'message': 'prompt is too long: 210000 tokens'}}))
        self.assertIn('bytes too large', classify_provider_error(413, {}))
        self.assertIn('retry the same', classify_provider_error(429, {}))
        self.assertIn('other client error', classify_provider_error(400, {'error': {'message': 'invalid tool schema'}}))


if __name__ == '__main__':
    unittest.main()
