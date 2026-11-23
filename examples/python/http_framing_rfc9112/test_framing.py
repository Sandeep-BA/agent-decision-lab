"""Tests for the RFC 9112 framing model. Author: Sandeep Belgavi."""
import unittest

import framing as F

HEAD = b'POST /returns HTTP/1.1\r\nHost: shop.example\r\n'


class FramingTest(unittest.TestCase):
    def test_single_headers_frame_the_same_body(self):
        self.assertEqual(F.frame(F.CASES['content-length only'])['body'], 'CASE-6201')
        self.assertEqual(F.frame(F.CASES['chunked only'])['body'], 'CASE-6201')

    def test_both_headers_rejected_in_strict_mode(self):
        with self.assertRaises(F.Reject) as e:
            F.frame(F.SMUGGLE, 'strict')
        self.assertEqual(e.exception.status, 400)

    def test_forwarding_mode_drops_content_length_and_uses_chunked(self):
        r = F.frame(F.SMUGGLE, 'forward')
        self.assertTrue(r['removed_content_length'])
        self.assertEqual(r['body'], '')
        self.assertTrue(r['leftover'].startswith('GET /admin/refunds HTTP/1.1'))

    def test_two_lenient_parsers_disagree_on_the_same_bytes(self):
        front, back = F.lenient(F.SMUGGLE, 'content-length'), F.lenient(F.SMUGGLE, 'chunked')
        self.assertEqual((len(front['body']), front['leftover']), (56, ''))
        self.assertEqual(back['body'], '')
        self.assertTrue(back['leftover'].startswith('GET /admin/refunds HTTP/1.1'))

    def test_chunked_must_be_final(self):
        with self.assertRaises(F.Reject):
            F.frame(F.CASES['gzip after chunked'], 'forward')

    def test_content_length_values(self):
        self.assertEqual(F.frame(F.CASES['duplicate equal lengths'])['body'], 'CASE-6201')
        for name in ('conflicting lengths', 'signed length'):
            with self.assertRaises(F.Reject):
                F.frame(F.CASES[name])
        with self.assertRaises(F.Reject):
            F.frame(HEAD + b'Content-Length: 20\r\n\r\nshort')

    def test_whitespace_before_colon_and_http10_te_rejected(self):
        for name in ('space before colon', 'TE in HTTP/1.0'):
            with self.assertRaises(F.Reject):
                F.frame(F.CASES[name], 'forward')

    def test_chunk_sizes_are_hex_and_validated(self):
        r = F.frame(HEAD + b'Transfer-Encoding: chunked\r\n\r\na\r\nCASE-62010\r\n0\r\n\r\n')
        self.assertEqual(r['body'], 'CASE-62010')
        with self.assertRaises(F.Reject):
            F.frame(HEAD + b'Transfer-Encoding: chunked\r\n\r\n-1\r\n\r\n')


if __name__ == '__main__':
    unittest.main()
