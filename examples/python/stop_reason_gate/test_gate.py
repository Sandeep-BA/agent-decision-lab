"""Tests for the stop-reason gate. Author: Sandeep Belgavi."""
import json
import unittest
from gate import FIXTURES, FULL_TEXT, TRUNCATED_TEXT, accept_json, classify, naive_repair


class StopReasonGateTest(unittest.TestCase):
    def test_every_truncated_fixture_is_refused(self):
        for api, body in FIXTURES.items():
            r = accept_json(api, body, ('overdue',))
            self.assertFalse(r['ok'], api)
            self.assertEqual(r['category'], 'truncated', api)

    def test_truncated_text_is_not_json(self):
        with self.assertRaises(json.JSONDecodeError):
            json.loads(TRUNCATED_TEXT)

    def test_naive_repair_silently_drops_items(self):
        self.assertEqual(naive_repair(TRUNCATED_TEXT), {'overdue': ['CASE-4101', 'CASE-4102']})
        self.assertEqual(len(json.loads(FULL_TEXT)['overdue']), 5)

    def test_complete_output_parses(self):
        body = {'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': FULL_TEXT}]}
        self.assertTrue(accept_json('anthropic', body, ('overdue',))['ok'])

    def test_unknown_reason_is_not_complete(self):
        body = {'candidates': [{'finishReason': 'SOMETHING_NEW', 'content': {'parts': [{'text': FULL_TEXT}]}}]}
        self.assertEqual(accept_json('gemini', body)['category'], 'unknown')

    def test_context_window_stop_is_truncation(self):
        body = {'stop_reason': 'model_context_window_exceeded', 'content': [{'type': 'text', 'text': FULL_TEXT}]}
        self.assertEqual(classify('anthropic', body)[0], 'truncated')

    def test_tool_and_pause(self):
        self.assertEqual(classify('openai-chat', {'choices': [{'finish_reason': 'tool_calls', 'message': {'content': None}}]})[0], 'tool')
        self.assertEqual(classify('anthropic', {'stop_reason': 'pause_turn', 'content': []})[0], 'paused')

    def test_missing_key_after_complete(self):
        body = {'choices': [{'finish_reason': 'stop', 'message': {'content': '{"other": 1}'}}]}
        self.assertEqual(accept_json('openai-chat', body, ('overdue',))['action'], "missing keys ['overdue']")


if __name__ == '__main__':
    unittest.main()
