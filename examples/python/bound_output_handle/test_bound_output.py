"""Tests for the bound output writer. Author: Sandeep Belgavi."""
import os
import tempfile
import unittest
from unittest import mock
import bound_output as b


class BoundOutputTest(unittest.TestCase):
    def test_plain_run_writes_result(self):
        r = b.scenario(b.bound_write, b.no_attack)
        self.assertEqual((r["result"], r["result_file"]), ("ok", "Summary for CASE-9050\n"))

    def test_late_write_overwrites_settings_through_planted_link(self):
        r = b.scenario(b.late_write, b.planted_before_start, True)
        self.assertEqual(r["settings"], "Summary for CASE-9050\n")

    def test_bound_write_refuses_planted_link(self):
        r = b.scenario(b.bound_write, b.planted_before_start, True)
        self.assertTrue(r["result"].startswith("refused"))
        self.assertEqual(r["settings"], "refund_limit=50\n")

    def test_late_write_follows_relink_during_work(self):
        r = b.scenario(b.late_write, b.relink_during_work)
        self.assertEqual(r["settings"], "Summary for CASE-9050\n")

    def test_bound_write_survives_relink_during_work(self):
        r = b.scenario(b.bound_write, b.relink_during_work)
        self.assertEqual(r["settings"], "refund_limit=50\n")

    def test_identity_change_is_refused(self):
        d = tempfile.mkdtemp()
        out = os.path.join(d, "result.md")
        real_stat = os.stat

        def swapped(path, *a, **k):
            st = real_stat(path, *a, **k)
            fake = list(st)
            fake[1] = st.st_ino + 1
            return os.stat_result(fake)

        def work():
            mock.patch("os.stat", swapped).start()

        try:
            with self.assertRaises(b.UnsafeOutput):
                b.bound_write(out, work, "x")
        finally:
            mock.patch.stopall()

    def test_removed_output_is_refused(self):
        d = tempfile.mkdtemp()
        out = os.path.join(d, "result.md")
        with mock.patch("os.stat", side_effect=FileNotFoundError):
            with self.assertRaises(b.UnsafeOutput):
                b.bound_write(out, lambda: None, "x")


if __name__ == "__main__":
    unittest.main()
