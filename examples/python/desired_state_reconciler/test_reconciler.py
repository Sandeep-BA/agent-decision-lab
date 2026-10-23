"""Tests for the desired-state reconciler. Standard library unittest only.

Author: Sandeep Belgavi.
"""
import unittest
from datetime import datetime, timezone

from reconciler import Store, reconcile, reconcile_once, active_set

DESIRED = {
    "principal": "contractor:erika",
    "grants": [{"project": "atlas", "role": "reader"},
               {"project": "orion", "role": "reader"},
               {"project": "vega", "role": "reader"}],
    "expires_at": "2026-10-30T00:00:00Z",
}
BEFORE = datetime(2026, 10, 23, tzinfo=timezone.utc)
AFTER = datetime(2026, 10, 31, tzinfo=timezone.utc)


def fresh(idempotent=True, drift=1):
    s = Store(idempotent=idempotent)
    for i in range(drift):
        s.add(f"legacy{i + 1}:reader")
    return s


class ReconcileTests(unittest.TestCase):
    def test_converges_and_corrects_drift(self):
        s = fresh()
        res = reconcile(DESIRED, s, BEFORE, passes=2)
        self.assertTrue(res.converged)
        self.assertEqual(res.gap, 0)
        self.assertNotIn("legacy1:reader", s.current())
        self.assertEqual(s.current(), {"atlas:reader", "orion:reader", "vega:reader"})

    def test_second_pass_is_a_noop(self):
        s = fresh(drift=0)
        reconcile(DESIRED, s, BEFORE, passes=1)
        applied = reconcile_once(DESIRED, s, BEFORE)
        self.assertEqual(applied, 0)             # idempotent: nothing left to do

    def test_crash_recovered_by_next_pass(self):
        s = fresh()
        res = reconcile(DESIRED, s, BEFORE, passes=2, crash_after=1)
        self.assertTrue(res.converged)
        one_pass = reconcile(DESIRED, fresh(), BEFORE, passes=1, crash_after=1)
        self.assertEqual(one_pass.gap, 3)        # one pass cannot recover the crash

    def test_expiry_removes_every_grant(self):
        s = fresh(drift=0)
        for g in DESIRED["grants"]:
            s.add(f"{g['project']}:{g['role']}")
        res = reconcile(DESIRED, s, AFTER, passes=2)
        self.assertEqual(active_set(DESIRED, AFTER), set())
        self.assertEqual(s.current(), set())
        self.assertTrue(res.converged)

    def test_stale_reads_need_idempotency(self):
        idem = reconcile(DESIRED, fresh(idempotent=True), BEFORE, passes=2, stale=True)
        self.assertEqual(idem.duplicate_applies, 0)
        self.assertTrue(idem.converged)
        non = reconcile(DESIRED, fresh(idempotent=False), BEFORE, passes=2, stale=True, crash_after=6)
        self.assertEqual(non.duplicate_applies, 3)


if __name__ == "__main__":
    unittest.main()
