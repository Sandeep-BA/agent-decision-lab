# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import unittest
from correlate import Client, kind, run, scenario


class CorrelateTest(unittest.TestCase):
    def setUp(self):
        self.r = run()

    def test_naive_client_resolves_its_own_request_with_the_servers_rejection(self):
        for st in (409, 200):
            s = self.r[f'naive_{st}']
            self.assertEqual((s['request_7_resolved_with'], s['request_7_resolved_via']), ('error', f'body of reply POST (HTTP {st})'))

    def test_naive_client_then_drops_the_real_result(self):
        self.assertIn('response to our request POST: result id 7 matches nothing pending; dropped', self.r['naive_409']['log'])

    def test_strict_client_rejects_non_acknowledgements(self):
        for st in (409, 200):
            s = self.r[f'strict_{st}']
            self.assertEqual(s['reply_outcome'], f'error: expected acknowledgement, got HTTP {st}')
            self.assertEqual(s['request_7_resolved_with'], 'result')

    def test_both_acknowledgement_statuses_are_accepted(self):
        for mode in ('naive', 'strict'):
            for st in (202, 204):
                self.assertEqual(self.r[f'{mode}_{st}']['reply_outcome'], 'acknowledged')

    def test_message_kinds(self):
        self.assertEqual([kind(m) for m in ({'id': 1, 'method': 'a'}, {'method': 'b'}, {'id': 1, 'result': {}}, {'id': 1, 'error': {}})],
                         ['request', 'notification', 'result', 'error'])

    def test_unrelated_ids_are_unaffected(self):
        c = Client(strict=False)
        c.send_request(8, 'tools/list')
        c.post_reply({'id': 7, 'result': {}}, 409, {'id': 7, 'error': {'code': -32600}})
        self.assertEqual(c.pending, {8: 'tools/list'})


if __name__ == '__main__':
    unittest.main()
