"""Tests for bulkjob.py. Author: Sandeep Belgavi."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bulkjob as bj


class BulkJobTest(unittest.TestCase):
    def test_preview_counts_and_revision_changes_the_hash(self):
        db = bj.catalogue()
        first, revised = bj.preview(db, bj.REQUEST), bj.preview(db, bj.REVISED)
        self.assertEqual(first['count'], 10)
        self.assertEqual(revised['count'], 7)          # three books already at 40% are excluded
        self.assertNotEqual(first['hash'], revised['hash'])

    def test_preview_changes_nothing(self):
        db = bj.catalogue()
        before = db.execute('SELECT SUM(version), SUM(discount_pct) FROM books').fetchone()
        bj.preview(db, bj.REQUEST)
        self.assertEqual(db.execute('SELECT SUM(version), SUM(discount_pct) FROM books').fetchone(), before)

    def test_filters_outside_the_allow_list_are_refused(self):
        db = bj.catalogue()
        for spec in ({'filter': [('id; DROP TABLE books', '=', 1)], 'set': {'tag': 'x'}},
                     {'filter': [('publisher', 'LIKE', '%')], 'set': {'tag': 'x'}},
                     {'filter': [('publisher', '=', 'x')], 'set': {'version': 1}}):
            with self.assertRaises(ValueError):
                bj.preview(db, spec)

    def test_approval_must_match_the_manifest(self):
        db = bj.catalogue()
        first, revised = bj.preview(db, bj.REQUEST), bj.preview(db, bj.REVISED)
        with self.assertRaises(PermissionError):
            bj.run(db, revised, first['hash'])

    def test_rows_changed_after_the_preview_are_skipped(self):
        db = bj.catalogue()
        plan = bj.preview(db, bj.REVISED)
        changed = plan['rows'][2][0]
        with db:
            db.execute('UPDATE books SET discount_pct = 20, version = version + 1 WHERE id = ?', (changed,))
        applied, skipped, _ = bj.run(db, plan, plan['hash'])
        self.assertEqual((applied, skipped), (6, [changed]))
        self.assertEqual(db.execute('SELECT discount_pct FROM books WHERE id = ?', (changed,)).fetchone()[0], 20)

    def test_interrupted_job_resumes_without_reapplying(self):
        db = bj.catalogue()
        plan = bj.preview(db, bj.REVISED)
        a1, _, b1 = bj.run(db, plan, plan['hash'], batch_size=5, stop_after=1)
        a2, _, b2 = bj.run(db, plan, plan['hash'], batch_size=5)
        a3, _, b3 = bj.run(db, plan, plan['hash'], batch_size=5)
        self.assertEqual((a1, b1, a2, b2, a3, b3), (5, 1, 2, 1, 0, 0))
        tagged = db.execute("SELECT COUNT(*) FROM books WHERE tag = 'clearance' AND discount_pct = 30").fetchone()[0]
        self.assertEqual(tagged, 7)
        self.assertEqual(db.execute('SELECT MAX(version) FROM books').fetchone()[0], 2)   # each row updated once


if __name__ == '__main__':
    unittest.main()
