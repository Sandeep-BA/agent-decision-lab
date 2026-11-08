# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

import unittest

from resume import RunManifest, resume_action

LIVE = {"agent-2026.11.2", "agent-2026.11.3"}
MIG = {(3, 4)}


class ResumeTest(unittest.TestCase):
    def action(self, bundle, schema):
        return resume_action(RunManifest("r1", bundle, schema), LIVE, MIG, 4)[0]

    def test_pin_when_bundle_is_live(self):
        self.assertEqual(self.action("agent-2026.11.2", 3), "pin")

    def test_migrate_when_bundle_is_gone_and_a_migration_exists(self):
        self.assertEqual(self.action("agent-2026.10.9", 3), "migrate")

    def test_close_out_for_anything_unforeseen(self):
        self.assertEqual(self.action("agent-2026.10.9", 2), "close_out")
        self.assertEqual(self.action("agent-unknown", 99), "close_out")

    def test_reason_is_recorded(self):
        _, reason = resume_action(RunManifest("r1", "x", 2), LIVE, MIG, 4)
        self.assertIn("schema 2", reason)


if __name__ == "__main__":
    unittest.main()
