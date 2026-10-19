"""Tests for the agent outbox journal model. Author: Sandeep Belgavi."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outbox_journal import Settings, simulate  # noqa: E402


def run(**kw):
    result, _trace = simulate(Settings(**kw))
    return result


class SafeguardsOn(unittest.TestCase):
    def assertClean(self, r):
        self.assertEqual(r["refunds"], 1)
        self.assertEqual(r["ledger_entries"], 1)
        self.assertEqual((r["duplicate_refunds"], r["lost_events"], r["duplicate_postings"]), (0, 0, 0))

    def test_clean_run(self):
        r = run()
        self.assertClean(r)
        self.assertEqual(r["deliveries"], 1)
        self.assertEqual(r["tool_calls"], 1)

    def test_crash_before_commit_rolls_back_and_resumes(self):
        r = run(crash_at="before_commit")
        self.assertClean(r)
        self.assertEqual(r["resumes"], 1)
        self.assertEqual(r["tool_calls"], 2)

    def test_crash_after_commit_is_skipped_on_resume(self):
        r = run(crash_at="after_commit")
        self.assertClean(r)
        self.assertEqual(r["tool_calls"], 1)

    def test_restart_from_scratch_is_saved_by_the_step_key(self):
        r = run(crash_at="after_commit", resume=False)
        self.assertClean(r)
        self.assertEqual(r["tool_calls"], 2)

    def test_agent_retry_is_harmless_with_the_step_key(self):
        r = run(agent_retry=True)
        self.assertClean(r)
        self.assertEqual(r["tool_calls"], 2)

    def test_relay_crash_delivers_twice_and_posts_once(self):
        r = run(crash_at="relay_between")
        self.assertEqual(r["deliveries"], 2)
        self.assertClean(r)


class SafeguardsOff(unittest.TestCase):
    def test_no_transaction_leaves_an_orphan_refund(self):
        r = run(crash_at="before_commit", atomic=False)
        self.assertEqual(r["duplicate_refunds"], 1)
        self.assertEqual(r["lost_events"], 1)

    def test_restart_without_step_key_repeats_the_refund(self):
        r = run(crash_at="after_commit", resume=False, step_key=False)
        self.assertEqual(r["refunds"], 2)
        self.assertEqual(r["duplicate_refunds"], 1)
        self.assertEqual(r["duplicate_postings"], 0, "consumer dedup cannot repair a duplicate effect")

    def test_agent_retry_without_step_key_repeats_the_refund(self):
        self.assertEqual(run(agent_retry=True, step_key=False)["duplicate_refunds"], 1)

    def test_relay_crash_without_dedup_posts_twice(self):
        self.assertEqual(run(crash_at="relay_between", consumer_dedup=False)["duplicate_postings"], 1)

    def test_mark_then_publish_loses_the_event(self):
        r = run(crash_at="relay_between", relay_order="mark_then_publish")
        self.assertEqual(r["deliveries"], 0)
        self.assertEqual(r["lost_events"], 1)


if __name__ == "__main__":
    unittest.main()
