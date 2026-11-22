# Author: Sandeep Belgavi. Expected outcomes quoted in the article and README.
import json
import unittest
from fields import CHUNKS, complete_fields, naive_repair, run


class FieldsTest(unittest.TestCase):
    def setUp(self):
        self.steps = run()

    def test_naive_preview_shows_a_prefix_of_the_action(self):
        self.assertEqual(self.steps[0]['naive']['action'], 'ref')
        self.assertNotIn('action', self.steps[0]['complete'])

    def test_amount_12_is_never_reported_complete(self):
        self.assertEqual(self.steps[1]['naive']['amount'], 12)
        self.assertNotIn('amount', self.steps[1]['complete'])
        self.assertEqual(self.steps[2]['complete']['amount'], 125)

    def test_open_nested_object_is_not_complete(self):
        self.assertEqual(self.steps[2]['naive']['items'], [{'sku': 'BK-7'}])
        self.assertNotIn('items', self.steps[2]['complete'])

    def test_final_result_matches_a_full_parse(self):
        self.assertEqual(self.steps[-1]['complete'], json.loads(''.join(CHUNKS)))

    def test_escaped_quote_inside_a_string(self):
        q = chr(92) + '"'
        buf = '{"note": "says ' + q + 'torn' + q + ' cover", "amount": 3'
        self.assertEqual(complete_fields(buf), {'note': 'says "torn" cover'})

    def test_every_cut_reports_only_final_values(self):
        full = ''.join(CHUNKS)
        expected = json.loads(full)
        self.assertEqual(len(full), 112)
        for cut in range(1, len(full)):
            for key, value in complete_fields(full[:cut]).items():
                self.assertEqual(expected[key], value, (cut, key))

    def test_literal_waits_for_a_delimiter(self):
        self.assertEqual(complete_fields('{"urgent": tru'), {})
        self.assertEqual(complete_fields('{"urgent": true,'), {'urgent': True})
        self.assertIsNone(naive_repair('{"urgent": tru'))


if __name__ == '__main__':
    unittest.main()
