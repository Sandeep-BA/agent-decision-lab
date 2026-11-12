"""Author: Sandeep Belgavi. Model expectations, including agreement with the recorded loopback probe."""
import unittest
from redirect_model import follow

ALL = {"authorization", "api-key-header", "body"}
A, B = "https://auth.example.test/token", "https://login.example.net/token"


class RedirectModelTests(unittest.TestCase):
    def test_307_and_308_resend_body_cross_origin(self):
        for client in ("fetch", "requests"):
            for st in (307, 308):
                _, m, d, _ = follow(client, st, "POST", A, B, ALL)
                self.assertEqual((m, d), ("POST", {"api-key-header", "body"}), (client, st))

    def test_302_and_303_drop_the_body(self):
        for client in ("fetch", "requests"):
            for st in (301, 302, 303):
                _, m, d, _ = follow(client, st, "POST", A, B, ALL)
                self.assertEqual((m, d), ("GET", {"api-key-header"}), (client, st))

    def test_same_origin_keeps_authorization(self):
        _, _, d, _ = follow("fetch", 307, "POST", A, "https://auth.example.test/v2/token", ALL)
        self.assertEqual(d, ALL)

    def test_http_to_https_differs_between_clients(self):
        _, _, f, _ = follow("fetch", 301, "GET", "http://api.example.test/x", "https://api.example.test/x", {"authorization"})
        _, _, r, _ = follow("requests", 301, "GET", "http://api.example.test/x", "https://api.example.test/x", {"authorization"})
        self.assertEqual((f, r), (set(), {"authorization"}))

    def test_port_change_strips_in_both(self):
        for c in ("fetch", "requests"):
            _, _, d, _ = follow(c, 307, "GET", "https://api.example.test/x", "https://api.example.test:8443/x", {"authorization"})
            self.assertEqual(d, set(), c)

    def test_copy_all_and_no_follow(self):
        self.assertEqual(follow("copy-all", 302, "POST", A, B, ALL)[2], ALL)
        self.assertEqual(follow("no-follow", 307, "POST", A, B, ALL)[:3], (False, None, set()))

    def test_matches_recorded_probe(self):
        """local_probe.py recorded requests 2.33.1 and Node 22.17 fetch, 127.0.0.1 -> localhost."""
        recorded = {301: ("GET", False), 302: ("GET", False), 303: ("GET", False), 307: ("POST", True), 308: ("POST", True)}
        for client in ("fetch", "requests"):
            for st, (method, body) in recorded.items():
                _, m, d, _ = follow(client, st, "POST", "http://127.0.0.1:8001/token", "http://localhost:8002/collect", ALL)
                self.assertEqual((m, "body" in d, "authorization" in d, "api-key-header" in d), (method, body, False, True))


if __name__ == "__main__":
    unittest.main()
