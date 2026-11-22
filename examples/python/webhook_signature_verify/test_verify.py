# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import unittest
from verify import Verifier, run, sign


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.r = run()

    def test_raw_bytes_verify_and_a_redelivery_is_a_duplicate(self):
        self.assertEqual((self.r['raw_body'], self.r['redelivery_same_id']), ('accept', 'duplicate: already processed'))

    def test_reserialized_json_no_longer_matches(self):
        self.assertEqual(self.r['reserialized_body'], 'reject: no matching signature')
        self.assertEqual(self.r['reserialized_bytes'], [87, 98])

    def test_rotation_accepts_either_secret_and_rejects_tampering(self):
        self.assertEqual(self.r['old_secret_during_rotation'], 'accept')
        self.assertEqual(self.r['tampered_body'], 'reject: no matching signature')

    def test_replay_outside_tolerance_and_dot_in_id(self):
        self.assertEqual(self.r['captured_and_replayed_301s_later'], 'reject: timestamp outside tolerance')
        self.assertEqual(self.r['dot_in_id'], 'reject: malformed headers')

    def test_one_of_several_offered_signatures_may_match(self):
        k, body = b'k' * 32, b'{}'
        v = Verifier([k], now=lambda: 100)
        sigs = 'v1,AAAA ' + sign(k, 'msg_1', 100, body)
        self.assertEqual(v.verify({'webhook-id': 'msg_1', 'webhook-timestamp': '100', 'webhook-signature': sigs}, body), 'accept')

    def test_replay_cache_expiry_keeps_ids_for_twice_the_tolerance(self):
        clock = [1000]
        v = Verifier([b'k' * 32], now=lambda: clock[0])
        v.seen['msg_old'] = 1000
        clock[0] = 1000 + 600
        v.expire()
        self.assertIn('msg_old', v.seen)
        clock[0] = 1000 + 601
        v.expire()
        self.assertNotIn('msg_old', v.seen)


if __name__ == '__main__':
    unittest.main()
