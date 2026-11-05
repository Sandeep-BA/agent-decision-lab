"""Tests for sqs_partial_batch. Author: Sandeep Belgavi. Run: python -m unittest -v"""
import json, pathlib, unittest
from handler import handle
from queue_sim import run

DATA = json.loads((pathlib.Path(__file__).resolve().parent / 'fixtures.json').read_text(encoding='utf-8'))


def event(*bodies):
    return {'Records': [{'messageId': 'id%d' % i, 'body': json.dumps(b)} for i, b in enumerate(bodies)]}


class HandlerTest(unittest.TestCase):
    def test_reports_only_the_failed_record(self):
        store = {}
        result = handle(event({'request_id': 'R1', 'order_id': 'BK-1'}, {'request_id': 'R2'}, {'request_id': 'R3', 'order_id': 'BK-3'}), store)
        self.assertEqual(result, {'batchItemFailures': [{'itemIdentifier': 'id1'}]})
        self.assertEqual(sorted(store), ['R1', 'R3'])

    def test_fifo_reports_the_failure_and_everything_after_it(self):
        result = handle(event({'request_id': 'R1', 'order_id': 'BK-1'}, {'request_id': 'R2'}, {'request_id': 'R3', 'order_id': 'BK-3'}), {}, fifo=True)
        self.assertEqual([f['itemIdentifier'] for f in result['batchItemFailures']], ['id1', 'id2'])

    def test_success_is_an_empty_list(self):
        self.assertEqual(handle(event({'request_id': 'R1', 'order_id': 'BK-1'}), {}), {'batchItemFailures': []})

    def test_redelivery_does_not_apply_twice(self):
        store = {}
        e = event({'request_id': 'R1', 'order_id': 'BK-1'})
        handle(e, store); handle(e, store)
        self.assertEqual(store['R1']['applied'], 1)


class QueueTest(unittest.TestCase):
    def run_mode(self, mode):
        return run(DATA['messages'], mode, transient_failures=DATA['transient_failures'])

    def test_whole_batch_failure_dead_letters_good_messages(self):
        r = self.run_mode('raise')
        self.assertEqual(len(r['dead_lettered']), 10)
        self.assertEqual((r['deliveries'], r['redeliveries'], r['applied']), (50, 40, 9))

    def test_partial_response_dead_letters_only_the_poison_message(self):
        r = self.run_mode('partial')
        self.assertEqual(r['dead_lettered'], ['m07'])
        self.assertEqual((r['deliveries'], r['redeliveries'], r['applied']), (15, 5, 9))

    def test_unknown_item_identifier_fails_the_whole_batch(self):
        self.assertEqual(len(self.run_mode('partial_bad_id')['dead_lettered']), 10)

    def test_without_poison_whole_batch_mode_recovers_after_one_retry(self):
        messages = [m for m in DATA['messages'] if m['id'] != 'm07']
        r = run(messages, 'raise', transient_failures=DATA['transient_failures'])
        self.assertEqual((r['dead_lettered'], r['deliveries']), ([], 18))


if __name__ == '__main__':
    unittest.main()
