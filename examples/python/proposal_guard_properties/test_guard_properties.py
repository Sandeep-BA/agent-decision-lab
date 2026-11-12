"""Author: Sandeep Belgavi. Property-based tests (Hypothesis 6.170.15) for guard.py.
derandomize=True makes every run explore the same examples, so CI is reproducible."""
import unittest
from hypothesis import given, settings, strategies as st, HealthCheck
from guard import Order, Proposal, check, check_buggy, APPROVAL_THRESHOLD

amounts = st.integers(min_value=-1_000, max_value=2_000_000)
statuses = st.sampled_from(["delivered", "returned", "shipped", "cancelled"])
proposals = st.lists(st.tuples(st.integers(0, 7), amounts, st.sampled_from(["INR", "INR", "INR", "USD"])), max_size=12)
SETTINGS = settings(derandomize=True, max_examples=300, suppress_health_check=[HealthCheck.too_slow], deadline=None)


def run(guard, total, status, plan):
    order = Order("ORD-7781", total, status=status)
    decisions = []
    for pid, amount, cur in plan:
        decisions.append((amount, guard(order, Proposal(f"P-{pid}", "ORD-7781", amount, cur))))
    return order, decisions


class GuardProperties(unittest.TestCase):
    @SETTINGS
    @given(st.integers(1, 1_500_000), statuses, proposals)
    def test_accepted_total_never_exceeds_order_total(self, total, status, plan):
        order, decisions = run(check, total, status, plan)
        self.assertLessEqual(sum(a for a, d in decisions if d == "accept"), total)
        self.assertEqual(order.refunded, sum(a for a, d in decisions if d == "accept"))

    @SETTINGS
    @given(st.integers(1, 1_500_000), statuses, proposals)
    def test_nothing_above_threshold_is_accepted_automatically(self, total, status, plan):
        _, decisions = run(check, total, status, plan)
        self.assertTrue(all(a <= APPROVAL_THRESHOLD for a, d in decisions if d == "accept"))

    @SETTINGS
    @given(st.integers(1, 1_500_000), st.integers(1, 2_000_000), st.integers(1, 2_000_000))
    def test_rejection_for_size_is_monotonic(self, total, a, b):
        small, large = sorted((a, b))
        if check(Order("ORD-7781", total), Proposal("P-1", "ORD-7781", small)) == "reject:exceeds-remaining":
            self.assertEqual(check(Order("ORD-7781", total), Proposal("P-1", "ORD-7781", large)), "reject:exceeds-remaining")

    @SETTINGS
    @given(st.integers(1, 1_500_000), st.integers(1, 500_000))
    def test_replayed_proposal_is_a_duplicate(self, total, amount):
        order = Order("ORD-7781", total)
        first = check(order, Proposal("P-9", "ORD-7781", amount))
        second = check(order, Proposal("P-9", "ORD-7781", amount))
        if first == "accept":
            self.assertEqual(second, "duplicate")
        self.assertLessEqual(order.refunded, amount)

    def test_buggy_guard_is_caught_with_a_small_counterexample(self):
        """The cumulative property fails for check_buggy; record Hypothesis' shrunk example."""
        found = {}

        @SETTINGS
        @given(st.integers(1, 1_500_000), proposals)
        def prop(total, plan):
            _, decisions = run(check_buggy, total, "delivered", plan)
            accepted = sum(a for a, d in decisions if d == "accept")
            if accepted > total:
                found.setdefault("example", (total, plan))
            assert accepted <= total

        with self.assertRaises(AssertionError):
            prop()
        total, plan = found["example"]
        self.assertGreaterEqual(len(plan), 2)


if __name__ == "__main__":
    unittest.main()
