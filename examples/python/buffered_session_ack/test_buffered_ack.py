# Author: Sandeep Belgavi. Runs the real google-adk 2.15.0 BufferedSessionService; no model calls.
import asyncio
import unittest
import warnings
from buffered_ack import turn


def run(*args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return asyncio.run(turn(*args, **kwargs))


class BufferedAckTest(unittest.TestCase):
    def test_append_returns_before_the_store_has_anything(self):
        r = run('ack_after_append')
        self.assertEqual((r['events_in_session_object'], r['stored_at_ack'], r['stored_after_close']), (4, 0, 4))

    def test_flush_then_ack_means_the_store_has_the_turn(self):
        r = run('flush_then_ack')
        self.assertEqual((r['ack'], r['stored_at_ack']), ('done', 4))
        self.assertGreaterEqual(r['ack_ms'], 150)  # four writes of about 50 ms each, in order

    def test_failed_write_drops_later_events(self):
        r = run('flush_then_ack', fail_at=3)
        self.assertEqual((r['ack'], r['error'], r['stored_after_close']), ('error', 'SessionPersistenceError', 2))
        self.assertIn('store unavailable on write 3', r['cause'])

    def test_failure_is_reported_once(self):
        r = run('flush_then_ack', fail_at=3)
        self.assertEqual(r['aclose'], 'ok')  # flush_session already reported it

    def test_ack_after_append_says_done_and_learns_of_the_failure_only_at_close(self):
        r = run('ack_after_append', fail_at=3)
        self.assertEqual(r['ack'], 'done')
        self.assertTrue(r['aclose'].startswith('SessionPersistenceError'))
        self.assertEqual(r['stored_after_close'], 2)


if __name__ == '__main__':
    unittest.main()
