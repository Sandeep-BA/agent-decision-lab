"""Tests for the HTTP framing toys; they check the article's probe and rules table. Author: Sandeep Belgavi."""
import unittest

import framing as fr


class Desync(unittest.TestCase):
    def test_cl_front_te_back_leaves_g_on_the_connection(self):
        self.assertEqual(fr.desync(fr.lenient_cl_first, fr.lenient_te_first, fr.PROBE), 'GPOST /checkout HTTP/1.1')

    def test_same_parser_both_sides_agrees(self):
        self.assertEqual(fr.desync(fr.lenient_te_first, fr.lenient_te_first, fr.PROBE), 'POST /checkout HTTP/1.1')

    def test_probe_body_is_six_bytes(self):
        self.assertEqual(len(b'0\r\n\r\nG'), 6)


class StrictRules(unittest.TestCase):
    def rule(self, *headers):
        return fr.body_length_rule(list(headers))

    def assertRejects(self, code, *headers):
        with self.assertRaises(fr.Reject) as cm:
            self.rule(*headers)
        self.assertTrue(cm.exception.args[0].startswith(code), cm.exception.args[0])

    def test_both_headers_rejected(self):
        self.assertRejects('400', ('Content-Length', '6'), ('Transfer-Encoding', 'chunked'))

    def test_whitespace_before_colon_rejected(self):
        self.assertRejects('400', ('Transfer-Encoding ', 'chunked'))

    def test_chunked_not_final_rejected(self):
        self.assertRejects('400', ('Transfer-Encoding', 'chunked, gzip'))

    def test_obfuscated_coding_rejected(self):
        self.assertRejects('400', ('Transfer-Encoding', 'xchunked'))

    def test_other_codings_not_implemented(self):
        self.assertRejects('501', ('Transfer-Encoding', 'gzip, chunked'))

    def test_conflicting_lengths_rejected_identical_list_accepted(self):
        self.assertRejects('400', ('Content-Length', '6'), ('Content-Length', '7'))
        self.assertEqual(self.rule(('Content-Length', '6, 6')), ('length', 6))

    def test_non_ascii_digits_rejected(self):
        self.assertRejects('400', ('Content-Length', '\u00b2'))

    def test_plain_cases(self):
        self.assertEqual(self.rule(('Content-Length', '6')), ('length', 6))
        self.assertEqual(self.rule(('Transfer-Encoding', 'chunked')), ('chunked', None))
        self.assertEqual(self.rule(), ('length', 0))

    def test_strict_frames_a_clean_chunked_request(self):
        req = b'POST /search HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n5\r\natlas\r\n0\r\n\r\n'
        self.assertEqual(fr.strict(req)[1:], (b'atlas', b''))


if __name__ == '__main__':
    unittest.main()
