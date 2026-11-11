"""Tests for the Traefik v3.7.18 preflight model. Author: Sandeep Belgavi."""
import unittest
from preflight import REQUESTS, ROUTERS, basicauth_too_long, default_tls_settings_lost, sanitize, split_views

DOCUMENTED = [('./foo/bar', '/foo/bar'), ('/foo/../bar', '/bar'), ('/foo/bar//', '/foo/bar/'),
              ('/./foo/../bar//', '/bar/'), ('/foo/.;bar/baz', '/foo/baz'), ('/foo/..;bar/baz', '/baz'),
              ('/foo/;bar/baz', '/foo/baz')]


class PreflightTest(unittest.TestCase):
    def test_documented_examples(self):
        for raw, expected in DOCUMENTED:
            self.assertEqual(sanitize(raw), expected, raw)

    def test_old_behaviour_keeps_parameter_segments(self):
        self.assertEqual(sanitize('/foo/..;bar/baz', v3718=False), '/foo/..;bar/baz')

    def test_ordinary_segment_parameters_untouched(self):
        self.assertEqual(sanitize('/shop;jsessionid=ABC/cart'), '/shop;jsessionid=ABC/cart')

    def test_split_view_before_and_closed_after(self):
        rows = {(r['request'], r['traefik']): r for r in split_views(REQUESTS, ROUTERS)}
        before = rows[('/help/..;/help/admin/cases', 'before')]
        after = rows[('/help/..;/help/admin/cases', 'v3.7.18')]
        self.assertEqual((before['router'], before['backend_owner'], before['split_view']), ('help-public', 'help-admin', True))
        self.assertEqual((after['router'], after['middlewares'], after['split_view']), ('help-admin', ('staff-auth',), False))

    def test_routing_change_without_security_impact(self):
        rows = {(r['request'], r['traefik']): r for r in split_views(REQUESTS, ROUTERS)}
        self.assertEqual(rows[('/help/articles/;v=2/returns', 'before')]['forwarded'], '/help/articles/;v=2/returns')
        self.assertEqual(rows[('/help/articles/;v=2/returns', 'v3.7.18')]['forwarded'], '/help/articles/returns')

    def test_basicauth_limit_counts_bytes(self):
        self.assertEqual(basicauth_too_long({'a': 'x' * 1024, 'b': 'x' * 1025, 'c': '\u00e9' * 513}), ['b', 'c'])

    def test_default_tls_settings(self):
        cfg = {'providers': {'kubernetesIngressNGINX': {}}, 'tls': {'options': {'default': {'minVersion': 'VersionTLS12'}}}}
        self.assertEqual(default_tls_settings_lost(cfg), ['minVersion'])
        self.assertEqual(default_tls_settings_lost({'providers': {'kubernetesCRD': {}}, 'tls': cfg['tls']}), [])


if __name__ == '__main__':
    unittest.main()
