"""Author: Sandeep Belgavi. Tests for the version-checked agent write example (fixed interleaving, no model)."""
import json
import unittest

import writes as w


class OptimisticWriteTests(unittest.TestCase):
    def test_unconditional_write_loses_the_escalation(self):
        _, (version, rec) = w.scenario("unconditional")
        self.assertEqual(version, 9)
        self.assertEqual((rec["priority"], rec["note"], rec["status"]), ("P3", "", "resolved"))

    def test_coupled_status_change_conflicts_with_a_priority_change(self):
        result, (version, rec) = w.scenario("status_and_summary")
        self.assertEqual(result["status"], "conflict")
        self.assertEqual(result["changed_since_read"], ["note", "priority"])
        self.assertEqual(result["current_version"], 8)
        self.assertEqual((version, rec["status"], rec["priority"]), (8, "open", "P1"))

    def test_disjoint_change_merges_and_keeps_both(self):
        result, (version, rec) = w.scenario("summary_only")
        self.assertEqual(result, {"status": "ok", "version": 9})
        self.assertEqual((rec["priority"], rec["note"], rec["summary"]), ("P1", "Customer is a hospital", "Duplicate charge refunded"))

    def test_update_guard_rejects_a_write_between_select_and_update(self):
        db = w.connect(); w.seed(db)
        v, base = w.read_ticket(db, "T-4471")
        # Simulate a second writer committing after our check by advancing the version first.
        db.execute("UPDATE tickets SET version = 8 WHERE id = 'T-4471'")
        cur = db.execute("UPDATE tickets SET data = ?, version = version + 1 WHERE id = ? AND version = ?",
                         (json.dumps(base), "T-4471", v))
        self.assertEqual(cur.rowcount, 0)


if __name__ == "__main__":
    unittest.main()
