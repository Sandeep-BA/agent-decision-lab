"""Tests for the enum boundary companion. Author: Sandeep Belgavi."""
import json
import pathlib
import unittest

import enum_boundary as eb

HERE = pathlib.Path(__file__).resolve().parent


class Write(unittest.TestCase):
    def test_case_and_aliases_map_by_table(self):
        self.assertEqual(eb.canonical_reason(' Damaged '), 'damaged')
        self.assertEqual(eb.canonical_reason('damaged_in_transit'), 'damaged')
        self.assertEqual(eb.canonical_reason('incorrect_item'), 'wrong_item')

    def test_unknown_value_is_refused_with_the_allowed_list(self):
        r = eb.create_return('BK-301', 'water_damage')
        self.assertFalse(r['ok'])
        self.assertEqual(r['allowed'], ['changed_mind', 'damaged', 'not_as_described', 'wrong_item'])

    def test_the_legacy_layer_turns_damage_into_change_of_mind(self):
        self.assertEqual(eb.legacy_reason('damaged_in_transit'), 'changed_mind')
        self.assertEqual(eb.create_return('BK-301', 'damaged_in_transit')['reason'], 'damaged')


class Read(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads((HERE / 'fixtures' / 'order_partially_shipped.json').read_text(encoding='utf-8'))

    def test_unseen_status_parses_to_unknown_with_category(self):
        s = eb.read_status(self.payload)
        self.assertEqual((s.value, s.raw, s.category), ('UNKNOWN', 'partially_shipped', 'in_transit'))

    def test_strict_reader_throws(self):
        with self.assertRaises(ValueError):
            eb.strict_status(self.payload)

    def test_known_status_is_unchanged(self):
        s = eb.read_status({'status': 'shipped'})
        self.assertEqual((s.value, s.category), ('shipped', 'in_transit'))


if __name__ == '__main__':
    unittest.main()
