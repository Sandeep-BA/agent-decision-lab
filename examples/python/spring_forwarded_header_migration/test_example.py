"""Author: Sandeep Belgavi. Tests for the Spring Boot 4.2 forwarded-header checker."""
import unittest
from example import SAMPLES, check, parse_properties


def levels(result):
    return [f["level"] for f in result["findings"]]


class ForwardedHeaders(unittest.TestCase):
    def test_legacy_maps_native_to_web_server(self):
        r = check(parse_properties(SAMPLES["legacy_native"]))
        self.assertEqual(r["effective_strategy"], "web-server")
        self.assertIn("deprecated", levels(r))

    def test_both_properties_fail_startup(self):
        r = check(parse_properties(SAMPLES["both_set"]))
        self.assertIsNone(r["effective_strategy"])
        self.assertEqual(levels(r), ["startup-failure"])

    def test_prefix_requires_x_forwarded(self):
        self.assertIn("startup-failure", levels(check(parse_properties(SAMPLES["rfc_with_prefix"]))))

    def test_defaults_depend_on_cloud_platform(self):
        self.assertEqual(check({}, on_cloud_platform=True)["effective_strategy"], "web-server")
        local = check({})
        self.assertEqual(local["effective_strategy"], "none")
        self.assertIn("check", levels(local))

    def test_migrated_config_is_clean(self):
        r = check(parse_properties(SAMPLES["migrated"]))
        self.assertEqual((r["effective_strategy"], r["findings"]), ("web-server", []))

    def test_empty_internal_proxies_is_flagged(self):
        r = check(parse_properties("server.request.header.forwarded.strategy=web-server\nserver.tomcat.remoteip.internal-proxies=\n"))
        self.assertEqual(levels(r), ["risk"])

    def test_comments_and_case(self):
        p = parse_properties("# comment\n! also\nSERVER.FORWARD-HEADERS-STRATEGY = FRAMEWORK\n")
        self.assertEqual(check(p)["effective_strategy"], "framework")


if __name__ == "__main__":
    unittest.main()
