"""Tests for tool_definition_budget. Author: Sandeep Belgavi. Run: python -m unittest -v
Token-count tests need tiktoken and its o200k_base file; they are skipped when it cannot load."""
import json, unittest
from budget import deferred_prefix, run_cost
from catalog import tools

try:
    import tiktoken
    ENC = tiktoken.get_encoding('o200k_base')
except Exception:          # not installed, or offline without a cached encoding file
    ENC = None


class BudgetTest(unittest.TestCase):
    def test_uncached_cost_grows_with_every_step(self):
        self.assertEqual(run_cost(3378, 286, 12), 43968)

    def test_cached_cost_is_one_write_then_reads(self):
        self.assertAlmostEqual(run_cost(3378, 286, 12, cached=True), 3664 * 2.35)

    def test_a_tool_list_change_costs_another_write(self):
        self.assertAlmostEqual(run_cost(3378, 286, 12, cached=True, invalidations=1), 3664 * 3.5)

    def test_cheaper_read_multiplier(self):
        self.assertAlmostEqual(run_cost(1000, 0, 3, cached=True, read_mult=0.05), 1000 * (1.25 + 0.1))

    def test_deferred_prefix_adds_parts(self):
        self.assertEqual(deferred_prefix(830, 100, 286), 1216)

    def test_rejects_zero_steps(self):
        with self.assertRaises(ValueError):
            run_cost(1, 1, 0)


class CatalogTest(unittest.TestCase):
    def test_every_schema_is_a_closed_object_with_known_required_fields(self):
        for style in ('concise', 'verbose'):
            for t in tools(style):
                schema = t['input_schema']
                self.assertEqual(schema['type'], 'object')
                self.assertFalse(schema['additionalProperties'])
                self.assertTrue(set(schema['required']) <= set(schema['properties']), t['name'])

    def test_verbose_only_adds_text(self):
        concise, verbose = tools('concise'), tools('verbose')
        self.assertEqual([t['name'] for t in concise], [t['name'] for t in verbose])
        self.assertTrue(all(len(json.dumps(v)) > len(json.dumps(c)) for c, v in zip(concise, verbose)))


@unittest.skipIf(ENC is None, 'tiktoken o200k_base not available')
class TokenCountTest(unittest.TestCase):
    def test_counts_quoted_in_the_readme(self):
        from measure import always_loaded_tokens, report
        r = report(ENC)
        self.assertEqual((r['concise']['total'], r['verbose']['total']), (1327, 3378))
        self.assertEqual(always_loaded_tokens(ENC), 830)


if __name__ == '__main__':
    unittest.main()
