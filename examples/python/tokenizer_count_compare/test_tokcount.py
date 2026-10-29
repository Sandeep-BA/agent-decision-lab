"""Tests for tokenizer_count_compare. Author: Sandeep Belgavi.

The projection tests run offline with the standard library. The measurement test runs only when the
pinned packages and fetched tokenizer files are present, and checks the exact counts reported in the article.
"""
import importlib.util, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import projection

HAVE = (importlib.util.find_spec('tiktoken') and importlib.util.find_spec('tokenizers')
        and os.path.exists(os.path.join(HERE, 'tokenizer_files', 'Qwen_Qwen2.5-0.5B-Instruct.json')))


class ProjectionTest(unittest.TestCase):
    def test_ratios_are_per_kind(self):
        r = projection.ratios([('a', 'xx'), ('a', 'xxxx'), ('b', 'y')], len, lambda s: 2 * len(s))
        self.assertEqual(r, {'a': 2.0, 'b': 2.0})

    def test_unknown_kind_defaults_to_one(self):
        self.assertEqual(projection.projected_tokens({'z': 100}, {}), 100)

    def test_article_mix_is_about_1_27(self):
        self.assertAlmostEqual(projection.article_mix(), 1.268, places=3)


@unittest.skipUnless(HAVE, 'pinned tokenizers not installed or tokenizer files not fetched')
class MeasuredCountsTest(unittest.TestCase):
    def test_counts_match_the_article_table(self):
        import measure
        names, rows = measure.measure()
        by = {r['sample']: r for r in rows}
        self.assertEqual(by['English help-desk message']['o200k_base'], 93)
        self.assertEqual(by['Hindi message']['cl100k_base'], 149)
        self.assertEqual(by['Hindi message']['o200k_base'], 47)
        self.assertEqual(by['Kannada message']['Phi-3.5-mini'], 344)
        self.assertEqual(by['Hindi message inside JSON, ensure_ascii=True']['Qwen2.5'], 625)
        self.assertEqual(sum(r['o200k_base'] for r in rows), 1613)


if __name__ == '__main__':
    unittest.main()
