"""Offline tests for the truncation helpers. Author: Sandeep Belgavi. No server is contacted."""
import unittest
from truncation import RECORDED, kept_fraction, overflow, request_body


class TruncationTest(unittest.TestCase):
    def test_body_always_states_truncation(self):
        self.assertEqual(request_body('m', 'x')['truncation'], 'disabled')
        self.assertEqual(request_body('m', 'x', 'auto')['truncation'], 'auto')
        with self.assertRaises(ValueError):
            request_body('m', 'x', 'middle')

    def test_recorded_overflow_is_recognised(self):
        self.assertEqual(overflow(400, RECORDED['responses_disabled']), (27599, 4096))
        self.assertEqual(overflow(400, RECORDED['chat_truncate_false']), (27599, 4096))

    def test_embedded_phrase_is_not_an_overflow(self):
        body = {'error': {'message': 'Invalid input contains: request (887 tokens) exceeds the available context size (300 tokens), try increasing it'}}
        self.assertIsNone(overflow(400, body))

    def test_hosted_style_and_code(self):
        self.assertEqual(overflow(400, {'error': {'message': 'The prompt is too long: 100, model maximum context length: 90'}}), (100, 90))
        self.assertEqual(overflow(413, {'error': {'code': 'context_length_exceeded'}}), (-1, -1))
        self.assertIsNone(overflow(429, {'error': {'code': 'context_length_exceeded'}}))

    def test_auto_kept_about_seven_percent(self):
        f = kept_fraction(RECORDED['responses_auto']['usage']['input_tokens'], 27599)
        self.assertAlmostEqual(f, 0.0743, places=4)
        self.assertEqual(RECORDED['responses_auto']['response_status'], 'completed')


if __name__ == '__main__':
    unittest.main()
