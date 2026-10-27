"""Tests for the embedding-migration shadow example. Author: Sandeep Belgavi."""
import json
import unittest
from pathlib import Path

from shadow import NEW, OLD, Index, embed, evaluate, gap_by_bucket, overlap_at_k, recall_at_k, rrf

HERE = Path(__file__).resolve().parent


class ShadowEvaluation(unittest.TestCase):
    def test_low_overlap_can_hide_an_improvement(self):
        out = evaluate(3)
        self.assertEqual(out["mean_overlap"], 0.333)
        self.assertEqual(out["mean_recall_old"], 0.167)
        self.assertEqual(out["mean_recall_new"], 0.7)

    def test_query_from_the_other_model_is_refused(self):
        idx = Index(NEW)
        idx.add("c01", "refund policy")
        with self.assertRaises(ValueError):
            idx.search(embed("refund", OLD), 1, OLD)

    def test_rank_fusion_matches_the_guide(self):
        old = ["c7", "c2", "c9", "c4"]
        new = ["c2", "c11", "c7", "c5"]
        self.assertEqual(overlap_at_k(old, new, 4), 0.5)
        self.assertEqual(recall_at_k(new, {"c2", "c11"}, 4), 1.0)
        self.assertEqual(rrf(old, new)[:3], ["c2", "c7", "c11"])

    def test_snapshot_backfill_misses_the_newest_bucket(self):
        corpus = json.loads((HERE / "fixtures" / "corpus.json").read_text(encoding="utf-8"))
        modified = {d["id"]: d["modified"] for d in corpus}
        old_ids = [d["id"] for d in corpus]
        snapshot_ids = [d["id"] for d in corpus if d["modified"] < "2026-10-27"]
        gaps = gap_by_bucket(old_ids, snapshot_ids, modified)
        self.assertEqual(gaps, {"2026-10-27": ["c10", "c11", "c12"]})

    def test_vectors_of_two_models_differ_in_dimension_and_space(self):
        self.assertEqual(len(embed("refund", OLD)), 64)
        self.assertEqual(len(embed("refund", NEW)), 96)


if __name__ == "__main__":
    unittest.main()
