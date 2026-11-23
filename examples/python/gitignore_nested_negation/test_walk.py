"""Tests for the gitignore pruning walkers. Author: Sandeep Belgavi."""
import unittest

import walk as W


class WalkTest(unittest.TestCase):
    def test_naive_pruning_loses_the_reincluded_file(self):
        self.assertNotIn('logs/keep.txt', W.walk(W.TREE, 'prune_naive')['kept'])
        self.assertEqual(W.walk(W.TREE, 'prune_naive')['gitignores_read'], ['.gitignore'])

    def test_guarded_pruning_matches_git_semantics(self):
        self.assertEqual(W.walk(W.TREE, 'prune_guarded')['kept'], W.walk(W.TREE, 'git_like')['kept'])

    def test_guarded_pruning_still_prunes_where_no_negation_applies(self):
        r = W.walk(W.TREE, 'prune_guarded')
        self.assertIn('build/', r['pruned'])
        self.assertNotIn('build/.gitignore', r['gitignores_read'])

    def test_a_negation_cannot_reach_under_an_excluded_directory(self):
        for mode in ('git_like', 'prune_guarded'):
            self.assertNotIn('logs/sub/keep.txt', W.walk(W.TREE, mode)['kept'])

    def test_same_file_negation_disables_pruning(self):
        tree = {'.gitignore': 'logs/**\n!logs/keep.txt\n', 'logs/keep.txt': 'p', 'logs/a.txt': 'd'}
        self.assertEqual(W.walk(tree, 'prune_guarded')['kept'], ['.gitignore', 'logs/keep.txt'])

    def test_model_agrees_with_real_git(self):
        oracle = W.git_oracle()
        if oracle is None:
            self.skipTest('git not on PATH')
        self.assertEqual(oracle, W.walk(W.TREE, 'git_like')['kept'])
        tree = {'.gitignore': 'logs/**\n!logs/keep.txt\n', 'logs/keep.txt': 'p', 'logs/a.txt': 'd'}
        self.assertEqual(W.git_oracle(tree), W.walk(tree, 'git_like')['kept'])


if __name__ == '__main__':
    unittest.main()
