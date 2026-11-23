"""Author: Sandeep Belgavi. Expected outcomes for the tolerant reader example."""
import unittest
from decimal import Decimal
import reader as R


class TolerantReaderTest(unittest.TestCase):
    def test_both_readers_accept_the_unchanged_payload(self):
        self.assertEqual(R.strict_read(R.V1).status, 'shipped')
        v = R.tolerant_read(R.V1, R.Drift())
        self.assertEqual((v.order_id, v.status, v.total, v.currency), ('ORD-7001', 'shipped', Decimal('24.50'), 'EUR'))

    def test_additive_change_breaks_the_strict_mirror_only(self):
        with self.assertRaises(R.ContractViolation) as e:
            R.strict_read(R.V2)
        self.assertEqual(e.exception.path, 'carrier_events')
        d = R.Drift()
        v = R.tolerant_read(R.V2, d)
        self.assertEqual(v.status, 'escalate')
        self.assertEqual(v.raw_status, 'partially_shipped')
        self.assertEqual(d.unknown_fields, {'carrier_events': 1, 'gift_wrap': 1})
        self.assertEqual(d.unknown_statuses, {'partially_shipped': 1})

    def test_unknown_status_is_never_guessed_into_a_known_one(self):
        v = R.tolerant_read(dict(R.V1, status='lost_in_transit'), R.Drift())
        self.assertEqual(v.status, 'escalate')
        self.assertIn('route to a person', v.note)

    def test_removed_consumed_field_fails_loudly_with_its_path(self):
        with self.assertRaises(R.ContractViolation) as e:
            R.tolerant_read(R.V3, R.Drift())
        self.assertEqual((e.exception.path, e.exception.problem), ('total.amount', 'missing consumed field'))

    def test_malformed_consumed_value_fails_loudly(self):
        with self.assertRaises(R.ContractViolation) as e:
            R.tolerant_read(R.V4, R.Drift())
        self.assertEqual(e.exception.path, 'total.amount')

    def test_run_table_matches_the_article(self):
        rows = R.run()
        self.assertEqual([r['strict'][:9] for r in rows[:4]], ['ok status', 'violation', 'violation', 'violation'])
        self.assertEqual([r['tolerant'][:9] for r in rows[:4]], ['ok status', 'ok status', 'violation', 'violation'])
        self.assertEqual(rows[4]['drift']['unknown_statuses'], {'partially_shipped': 1})


if __name__ == '__main__':
    unittest.main()
