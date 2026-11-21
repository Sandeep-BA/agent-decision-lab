# Author: Sandeep Belgavi. Expected outcomes quoted in the article, README and lab.
import unittest
from dns_names import build_fixtures, decode_name, run_all, NameError_


class DnsNameTest(unittest.TestCase):
    def test_valid_name_and_next_offset(self):
        f = build_fixtures()['valid']
        r = decode_name(f['packet'], f['offset'])
        self.assertEqual((r['name'], r['next_offset'], r['hops'], r['wire_length']), ('help.books.example.com.', 42, 1, 24))

    def test_strict_refusals(self):
        r = run_all()
        self.assertIn('not before it', r['self_loop']['error'])
        self.assertIn('not before it', r['forward_pointer']['error'])
        self.assertIn('inside the header', r['header_pointer']['error'])
        self.assertIn('reserved 01 prefix', r['reserved_label']['error'])
        self.assertIn('257 octets', r['too_long']['error'])
        self.assertIn('only 5 remain', r['truncated']['error'])

    def test_hop_limit_catches_loops_when_forward_pointers_are_allowed(self):
        r = run_all(backward_only=False, max_hops=8)
        self.assertEqual(r['self_loop']['error'], 'more than 8 pointers')
        self.assertEqual(r['two_pointer_loop']['error'], 'more than 8 pointers')
        self.assertEqual((r['forward_pointer']['name'], r['forward_pointer']['next_offset']), ('com.', 14))

    def test_without_bounds_a_loop_never_ends(self):
        f = build_fixtures()['self_loop']
        with self.assertRaisesRegex(NameError_, 'loop forever'):
            decode_name(f['packet'], f['offset'], backward_only=False, max_hops=0)

    def test_length_bound_alone_does_not_stop_a_pure_pointer_loop(self):
        f = build_fixtures()['two_pointer_loop']
        with self.assertRaisesRegex(NameError_, 'loop forever'):
            decode_name(f['packet'], f['offset'], backward_only=False, max_hops=0, max_length=255)

    def test_header_check_can_be_disabled_to_show_the_risk(self):
        f = build_fixtures()['header_pointer']
        with self.assertRaises(NameError_) as ctx:
            decode_name(f['packet'], f['offset'], min_target=0)
        self.assertNotIn('inside the header', ctx.exception.args[0])


if __name__ == '__main__':
    unittest.main()
