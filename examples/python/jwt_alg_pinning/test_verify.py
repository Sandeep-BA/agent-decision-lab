# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

import unittest

from verify import Forged, sign_hs256, verify_header_chooses, verify_pinned

PUBLIC = "-----BEGIN PUBLIC KEY-----\nsynthetic-example\n-----END PUBLIC KEY-----\n"


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.forged = sign_hs256({"sub": "geetha", "role": "admin"}, PUBLIC.encode())

    def test_vulnerable_verifier_accepts_a_token_forged_with_the_public_key(self):
        self.assertEqual(verify_header_chooses(self.forged, PUBLIC)["role"], "admin")

    def test_pinned_verifier_rejects_the_wrong_algorithm(self):
        with self.assertRaises(Forged):
            verify_pinned(self.forged, PUBLIC)

    def test_vulnerable_verifier_still_rejects_a_wrong_key(self):
        with self.assertRaises(Forged):
            verify_header_chooses(sign_hs256({"sub": "x"}, b"other"), PUBLIC)


if __name__ == "__main__":
    unittest.main()
