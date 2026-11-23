"""Author: Sandeep Belgavi. Expected outcomes for the edge schema fit model (rules read from ADK Java v1.15.0 SchemaFit)."""
import unittest
import schema_fit as F

S = F.S


class SchemaFitTest(unittest.TestCase):
    def table(self):
        return {r['edge']: r['fits'] for r in F.run()}

    def test_widening_is_allowed_narrowing_is_not(self):
        t = self.table()
        self.assertTrue(t['integer into number'])
        self.assertFalse(t['number into integer'])

    def test_enums_must_be_subsets(self):
        t = self.table()
        self.assertTrue(t['enum subset'])
        self.assertFalse(t['enum superset'])
        self.assertIn("['other']", F.fits(*F.CASES[3][1:3])[1])

    def test_nullable_source_needs_a_nullable_target(self):
        self.assertFalse(self.table()['nullable into non-null'])
        self.assertTrue(F.fits(S('string', nullable=True), S('string', nullable=True))[0])

    def test_extra_keys_fit_an_open_target_but_not_a_closed_inferred_one(self):
        t = self.table()
        self.assertTrue(t['refund into wider open object'])
        self.assertFalse(t['refund into closed inferred record'])

    def test_required_keys_must_be_guaranteed(self):
        ok, why = F.fits(*F.CASES[7][1:3])
        self.assertFalse(ok)
        self.assertIn("['amount']", why)

    def test_what_the_build_cannot_see(self):
        t = self.table()
        self.assertTrue(t['map output into record input'])      # keys unknown until run time
        self.assertTrue(t['bounds ignored at build time'])       # 0 or 900 still fails at run time

    def test_nested_paths_are_reported(self):
        src = S('object', properties={'items': S('array', items=S('number'))}, required=['items'])
        dst = S('object', properties={'items': S('array', items=S('integer'))}, required=['items'])
        ok, why = F.fits(src, dst)
        self.assertEqual((ok, why), (False, '$.items[]: number does not fit integer'))


if __name__ == '__main__':
    unittest.main()
