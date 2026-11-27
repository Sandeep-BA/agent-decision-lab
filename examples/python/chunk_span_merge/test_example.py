"""Tests for chunk_span_merge. Author: Sandeep Belgavi."""
import io, json, unittest
from contextlib import redirect_stdout
from pathlib import Path
import example as ex


class ChunkSpanMerge(unittest.TestCase):
    def test_report_matches_recorded_expected_output(self):
        with redirect_stdout(io.StringIO()):
            report = ex.main()
        self.assertEqual(report, json.loads((Path(__file__).parent / 'expected.json').read_text(encoding='utf-8')))

    def test_consecutive_chunks_share_the_overlap(self):
        chunks = ex.chunk('d', ' '.join(ex.DOCS['returns-policy']))
        for a, b in zip(chunks, chunks[1:]):
            self.assertLess(b['start'], a['end'])
            self.assertLessEqual(a['end'] - b['start'], ex.OVERLAP)

    def test_chunks_cover_the_whole_document(self):
        text = ' '.join(ex.DOCS['shipping-guide'])
        chunks = ex.chunk('d', text)
        self.assertEqual(chunks[0]['start'], 0)
        self.assertEqual(chunks[-1]['end'], len(text))

    def test_exact_text_dedup_misses_overlapping_chunks(self):
        plain, _ = ex.fill(ex.ranked(ex.build_index()), budget=None, merge=False)
        self.assertEqual(ex.exact_text_dedup(plain), len(plain))
        self.assertLess(ex.unique_chars(plain), sum(len(p['text']) for p in plain))

    def test_merge_joins_touching_spans_and_keeps_best_score(self):
        hits = [{'doc': 'returns-policy', 'start': 0, 'end': 100, 'score': 0.2},
                {'doc': 'returns-policy', 'start': 80, 'end': 200, 'score': 0.9},
                {'doc': 'returns-policy', 'start': 300, 'end': 350, 'score': 0.5}]
        merged = ex.merge_spans(hits)
        self.assertEqual([(m['start'], m['end'], m['score'], m['parts']) for m in merged], [(0, 200, 0.9, 2), (300, 350, 0.5, 1)])

    def test_merged_context_has_no_repeated_text_and_fits_the_budget(self):
        ranking = ex.ranked(ex.build_index())
        plain, used = ex.fill(ranking, budget=None, merge=False)
        merged, used_m = ex.fill(ranking, budget=used, merge=True)
        self.assertLessEqual(used_m, used)
        self.assertEqual(ex.unique_chars(merged), used_m)
        self.assertGreater(len({m['doc'] for m in merged}), len({p['doc'] for p in plain}))


if __name__ == '__main__':
    unittest.main()
