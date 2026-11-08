# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

import unittest

from hostmatch import is_acr_host, unsafe_is_acr


class HostMatchTest(unittest.TestCase):
    def test_lookalike_passes_the_unsafe_check(self):
        self.assertTrue(unsafe_is_acr("x.azurecr.io.attacker.example"))

    def test_lookalike_fails_the_exact_check(self):
        for host in ("x.azurecr.io.attacker.example", "azurecr.io", "x.azurecr.io@attacker.example", "evil.com/x.azurecr.io", ""):
            self.assertFalse(is_acr_host(host), host)

    def test_real_hosts_pass(self):
        for host in ("store.azurecr.io", "store.azurecr.io:443", "STORE.AZURECR.IO", "mcr.microsoft.com", "a.b.azurecr.us"):
            self.assertTrue(is_acr_host(host), host)

    def test_empty_labels_fail(self):
        self.assertFalse(is_acr_host("a..azurecr.io"))


if __name__ == "__main__":
    unittest.main()
