"""Author: Sandeep Belgavi. Expected outcomes for the undo-window example (SQLite, synthetic data)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import actions  # noqa: E402


class UndoWindowTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "a.db")
        actions.setup(self.path).close()

    def tearDown(self):
        self.dir.cleanup()

    def test_exactly_one_of_cancel_and_claim_wins(self):
        winners = {"cancel": 0, "claim": 0}
        for trial in range(60):
            out = actions.race_once(self.path, now=10_000 + trial)
            cancelled = out["cancel"]["result"] == "cancelled"
            claimed = out["claim"] is not None
            self.assertNotEqual(cancelled, claimed, out)       # never both, never neither
            winners["cancel" if cancelled else "claim"] += 1
        self.assertEqual(sum(winners.values()), 60)

    def test_cancel_before_due_and_too_late_after_done(self):
        conn = actions.connect(self.path)
        a = actions.schedule(conn, "return_label", "BK-1044", now=0)
        self.assertEqual(actions.cancel(conn, a, "Geetha")["result"], "cancelled")
        self.assertIsNone(actions.claim_due(conn, now=10_000))
        b = actions.schedule(conn, "refund", "BK-1054", now=0)
        self.assertIsNone(actions.claim_due(conn, now=899))     # not due yet
        claimed = actions.claim_due(conn, now=900)
        actions.execute(conn, claimed)
        late = actions.cancel(conn, b, "Geetha")
        self.assertEqual((late["result"], late["state"]), ("too_late", "done"))
        conn.close()

    def test_replacement_executor_reuses_the_idempotency_key(self):
        conn = actions.connect(self.path)
        a = actions.schedule(conn, "refund", "BK-1055 refund 300", now=0)
        claimed = actions.claim_due(conn, now=900)
        # The first executor calls the downstream and crashes before marking the action done.
        conn.execute("INSERT OR IGNORE INTO downstream_call VALUES (?, ?)", ("agent-action-%d" % a, claimed[2]))
        key = actions.execute(conn, claimed)                    # the replacement repeats the call
        calls = conn.execute("SELECT count(*) FROM downstream_call WHERE idempotency_key = ?", (key,)).fetchone()[0]
        state = conn.execute("SELECT state FROM agent_action WHERE id = ?", (a,)).fetchone()[0]
        conn.close()
        self.assertEqual((calls, state), (1, "done"))


if __name__ == "__main__":
    unittest.main()
