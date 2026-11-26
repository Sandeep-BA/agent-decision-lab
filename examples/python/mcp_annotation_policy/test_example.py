"""Author: Sandeep Belgavi. Tests for host-owned MCP approval decisions."""
import json
import unittest
from pathlib import Path
from example import (CLASSES, SERVERS, TRUST, changed_listing, decide_all, definition_digest,
                     effective_hints, host_policy, main, naive)


class AnnotationPolicy(unittest.TestCase):
    def test_schema_defaults(self):
        self.assertEqual(effective_hints(None), {"readOnlyHint": False, "destructiveHint": True,
                                                 "idempotentHint": False, "openWorldHint": True})
        self.assertIsNone(effective_hints({"readOnlyHint": True})["destructiveHint"])

    def test_naive_policy_trusts_a_mislabelled_delete(self):
        self.assertEqual(decide_all(naive)["web-notes/delete_note"], "auto")

    def test_host_policy_ignores_untrusted_hints(self):
        self.assertEqual(decide_all(host_policy)["web-notes/delete_note"], "ask")

    def test_hint_can_only_tighten(self):
        self.assertEqual(decide_all(host_policy)["bookstore-orders/order_history"], "ask")
        self.assertEqual(decide_all(host_policy)["bookstore-orders/lookup_order"], "auto")

    def test_missing_annotations_mean_ask(self):
        self.assertEqual(decide_all(host_policy)["bookstore-orders/list_returns"], "ask")

    def test_review_is_pinned_to_definition(self):
        self.assertEqual(changed_listing()["web-notes/search_notes"], "ask")
        tool = SERVERS["web-notes"][0]
        self.assertEqual(definition_digest(tool), definition_digest(json.loads(json.dumps(tool))))

    def test_deny_wins(self):
        classes = dict(CLASSES)
        classes["bookstore-orders/lookup_order"] = ("deny", CLASSES["bookstore-orders/lookup_order"][1])
        self.assertEqual(host_policy("bookstore-orders", SERVERS["bookstore-orders"][0], TRUST, classes), "deny")

    def test_expected_file_matches(self):
        expected = json.loads(Path(__file__).with_name("expected.json").read_text(encoding="utf-8"))
        self.assertEqual(main(), expected)


if __name__ == "__main__":
    unittest.main()
