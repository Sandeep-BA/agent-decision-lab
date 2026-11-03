"""Author: Sandeep Belgavi. Expected outcomes for the write-skew example (SQLite, synthetic data)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import credits  # noqa: E402


class WriteSkewTest(unittest.TestCase):
    def run_race(self, grant, existing=1, cases=("CASE-4101", "CASE-4102")):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "c.db")
            credits.setup(path, existing=existing)
            return credits.race(grant, path, cases)

    def test_unguarded_breaks_the_limit(self):
        for _ in range(5):
            total, results = self.run_race(credits.grant_unguarded)
            self.assertEqual(total, 3)
            self.assertEqual(sorted(r["status"] for r in results.values()), ["granted", "granted"])

    def test_guarded_holds_the_limit(self):
        for _ in range(5):
            total, results = self.run_race(credits.grant_guarded)
            self.assertEqual(total, 2)
            self.assertEqual(sorted(r["status"] for r in results.values()), ["granted", "limit_reached"])

    def test_guarded_with_four_runs_and_no_credits(self):
        total, results = self.run_race(credits.grant_guarded, existing=0,
                                       cases=("CASE-4101", "CASE-4102", "CASE-4103", "CASE-4104"))
        self.assertEqual(total, 2)
        self.assertEqual(sorted(r["status"] for r in results.values()).count("limit_reached"), 2)

    def test_refusal_is_a_result_not_an_exception(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "c.db")
            credits.setup(path, existing=2)
            conn = credits.connect(path)
            out = credits.grant_guarded(conn, "geetha", "CASE-4109", 100)
            conn.close()
        self.assertEqual(out["status"], "limit_reached")
        self.assertIn("next_step", out)


if __name__ == "__main__":
    unittest.main()
