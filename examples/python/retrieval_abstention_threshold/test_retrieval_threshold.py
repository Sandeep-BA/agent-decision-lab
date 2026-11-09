"""Author: Sandeep Belgavi."""
import json, unittest
from pathlib import Path
from retrieval_threshold import report

ROWS = json.loads((Path(__file__).parent / 'fixtures.json').read_text(encoding='utf-8'))['retrieval']


class Threshold(unittest.TestCase):
    def test_high_score_can_be_a_false_accept(self):
        r = report(ROWS, 0.8)
        self.assertEqual((r['accepted'], r['false_accepts'], r['precision']), (2, 1, 0.5))

    def test_threshold_equality_accepts(self):
        self.assertEqual(report(ROWS, 0.85)['accepted'], 2)

    def test_empty_cases(self):
        self.assertIsNone(report(ROWS, 1)['precision'])
        self.assertIsNone(report([], 1)['coverage'])


if __name__ == '__main__':
    unittest.main()
