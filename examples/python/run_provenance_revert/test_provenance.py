"""Author: Sandeep Belgavi. Tests for run-provenance tagging and selective revert."""
import unittest

from provenance import apply_revert, connect, demo, plan_revert, write_field


def row(db, cid):
    return db.execute('SELECT status, credit, note FROM cases WHERE case_id = ?', (cid,)).fetchone()


class RevertTests(unittest.TestCase):
    def test_plan_restores_untouched_fields_and_flags_later_edits(self):
        plan = {(s.case_id, s.col): s.action for s in plan_revert(demo(), 'run-17', 'field')}
        self.assertEqual(plan, {('CASE-5201', 'status'): 'restore', ('CASE-5201', 'credit'): 'restore',
                                ('CASE-5202', 'status'): 'restore', ('CASE-5202', 'credit'): 'conflict'})

    def test_row_granularity_holds_back_the_whole_row(self):
        plan = {(s.case_id, s.col): s.action for s in plan_revert(demo(), 'run-17')}
        self.assertEqual(plan[('CASE-5202', 'status')], 'conflict')
        self.assertEqual(plan[('CASE-5201', 'status')], 'restore')

    def test_apply_keeps_the_human_correction_and_other_runs(self):
        db = demo()
        self.assertEqual(apply_revert(db, 'run-17', 'Jenya'), {'restore': 2, 'conflict': 2, 'already reverted': 0})
        self.assertEqual(row(db, 'CASE-5201'), ('open', 0, ''))
        self.assertEqual(row(db, 'CASE-5202'), ('approved', 15.0, ''))
        self.assertEqual(row(db, 'CASE-5203'), ('approved', 0, ''))

    def test_revert_is_idempotent_and_auditable(self):
        db = demo()
        apply_revert(db, 'run-17', 'Jenya')
        self.assertEqual(apply_revert(db, 'run-17', 'Jenya'), {'restore': 0, 'conflict': 2, 'already reverted': 2})
        actors = db.execute("SELECT DISTINCT actor FROM change_log WHERE run_id = 'revert-run-17'").fetchall()
        self.assertEqual(actors, [('Jenya',)])

    def test_two_writes_to_one_field_restore_the_value_before_the_first(self):
        db = connect()
        db.execute("INSERT INTO cases VALUES ('CASE-5301', 'open', 0, '')")
        write_field(db, 'run-20', 'returns-agent', 'CASE-5301', 'credit', 10.0)
        write_field(db, 'run-20', 'returns-agent', 'CASE-5301', 'credit', 30.0)
        apply_revert(db, 'run-20', 'Tanishka')
        self.assertEqual(row(db, 'CASE-5301'), ('open', 0, ''))

    def test_the_revert_itself_can_be_reverted(self):
        db = demo()
        apply_revert(db, 'run-17', 'Jenya')
        apply_revert(db, 'revert-run-17', 'Jenya')
        self.assertEqual(row(db, 'CASE-5201'), ('approved', 25.0, ''))

    def test_write_and_log_are_atomic(self):
        db = connect()
        db.execute("INSERT INTO cases VALUES ('CASE-5401', 'open', 0, '')")
        db.execute('CREATE TRIGGER boom BEFORE INSERT ON change_log BEGIN SELECT RAISE(ABORT, "log unavailable"); END')
        with self.assertRaises(Exception):
            write_field(db, 'run-21', 'returns-agent', 'CASE-5401', 'status', 'approved')
        self.assertEqual(row(db, 'CASE-5401'), ('open', 0, ''))


if __name__ == '__main__':
    unittest.main()
