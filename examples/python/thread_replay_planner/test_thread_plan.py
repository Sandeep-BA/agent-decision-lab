"""Author: Sandeep Belgavi."""
import unittest
from thread_plan import recovery_for, request_plan

HISTORY = [{'role': 'user', 'content': 'CASE-0042 old'}]
PENDING = [{'role': 'user', 'content': 'CASE-0042 new'}]


class Plan(unittest.TestCase):
    def test_create_and_continue_shapes(self):
        create = request_plan(HISTORY, PENDING, None, 'fixed', [])
        self.assertEqual(create['messages'], HISTORY + PENDING)
        self.assertEqual(create['thread'], {'type': 'create'})
        continuing = request_plan(HISTORY, PENDING, 'msg-synthetic', 'fixed', [])
        self.assertEqual(continuing['messages'], PENDING)
        self.assertNotIn('system', continuing)
        self.assertNotIn('tools', continuing)

    def test_recreation_does_not_mutate_history(self):
        create = request_plan(HISTORY, PENDING, None, 'fixed', [])
        create['messages'][0]['content'] = 'changed'
        self.assertEqual(HISTORY[0]['content'], 'CASE-0042 old')

    def test_documented_recoveries(self):
        self.assertEqual(recovery_for(404, 'thread_not_found'), 'replay_full_conversation')
        self.assertEqual(recovery_for(404, 'not_found_error'), 'surface_error')
        self.assertEqual(recovery_for(400, 'thread_fingerprint_mismatch'), 'fix_field_or_start_new_thread')
        self.assertEqual(recovery_for(stop_reason='refusal'), 'new_thread_without_refused_turn')
        self.assertEqual(recovery_for(), 'continue_normally')


if __name__ == '__main__':
    unittest.main()
