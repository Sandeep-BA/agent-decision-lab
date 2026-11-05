"""Tests for identifier_canonical_keys. Author: Sandeep Belgavi. Run: python -m unittest -v"""
import unittest, unicodedata
import demo
from canonical import Rejected, load_confusables, naive_keys, skeleton, username_key


class UsernameKeyTest(unittest.TestCase):
    def test_width_case_and_nfc_converge(self):
        for raw in ('Geetha', 'ＧＥＥＴＨＡ', 'GEETHA'):
            self.assertEqual(username_key(raw), 'geetha')
        self.assertEqual(username_key('tanishka.café'), username_key('tanishka.café'))

    def test_kelvin_sign_lowercases_to_ascii_k(self):
        self.assertEqual(username_key('dinKy'), 'dinky')

    def test_invisible_and_space_characters_are_rejected(self):
        for raw in ('geet‍ha', 'hansini ', 'han sini', '', '́abc'):
            with self.assertRaises(Rejected):
                username_key(raw)

    def test_sharp_s_is_kept_by_rfc8265_but_merged_by_casefold(self):
        self.assertNotEqual(username_key('jenya.straße'), username_key('jenya.strasse'))
        self.assertEqual(naive_keys('jenya.straße')['casefold_nfkc'], naive_keys('jenya.strasse')['casefold_nfkc'])

    def test_key_is_idempotent(self):
        for raw in ('Geetha', 'tanishka.café', 'dinKy', 'jenya.straße'):
            self.assertEqual(username_key(username_key(raw)), username_key(raw))


class SkeletonTest(unittest.TestCase):
    def test_cyrillic_lookalike_shares_a_skeleton_but_not_a_key(self):
        table = load_confusables()
        self.assertNotEqual(username_key('gеetha'), username_key('geetha'))
        self.assertEqual(skeleton('gеetha', table), skeleton('geetha', table))

    def test_skeleton_is_not_an_identity(self):
        table = load_confusables()
        self.assertEqual(skeleton('rn', table), skeleton('m', table))   # why a skeleton must never be the stored key


class ReplayTest(unittest.TestCase):
    def test_expected_counts_match_the_article(self):
        rows = demo.replay()
        counts = {s: sum(demo.wrong(r, s) for r in rows) for s in demo.STRATEGIES}
        self.assertEqual(counts, {'raw UNIQUE': 7, 'SQLite NOCASE': 5, 'lower()': 4, 'username_key': 0})
        self.assertEqual(sum(r['review'].startswith('looks like') for r in rows), 1)

    def test_sqlite_nocase_folds_ascii_only(self):
        rows = {r['name']: r for r in demo.replay()}
        self.assertEqual(rows['Geetha']['SQLite NOCASE'], 'duplicate')
        self.assertEqual(rows['dinKy']['SQLite NOCASE'], 'stored')


if __name__ == '__main__':
    unittest.main()
