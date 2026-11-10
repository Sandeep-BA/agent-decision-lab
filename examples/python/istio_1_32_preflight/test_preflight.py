"""Author: Sandeep Belgavi."""
import unittest
from preflight import envoyfilter_findings, sample_filter, timeout_findings


class Preflight(unittest.TestCase):
    def test_insert_patch_is_dropped_when_the_flag_is_on(self):
        (finding,) = envoyfilter_findings([sample_filter('INSERT_BEFORE')], httproute_auth_enabled=True)
        self.assertEqual(finding[3], 'high')
        self.assertIn('dropped', finding[4])

    def test_merge_patch_stops_applying(self):
        (finding,) = envoyfilter_findings([sample_filter('MERGE')], httproute_auth_enabled=True)
        self.assertIn('no longer applies', finding[4])

    def test_flag_off_is_informational(self):
        (finding,) = envoyfilter_findings([sample_filter('REPLACE')], httproute_auth_enabled=False)
        self.assertEqual(finding[3], 'info')

    def test_sidecar_patches_are_ignored(self):
        f = sample_filter('MERGE')
        f['spec']['configPatches'][0]['match']['context'] = 'SIDECAR_INBOUND'
        self.assertEqual(envoyfilter_findings([f], True), [])

    def test_timeouts(self):
        self.assertEqual(timeout_findings({}), [])                       # 90s header > 60s server
        (f,) = timeout_findings({'ISTIO_KUBE_HEADER_TIMEOUT': '45s'})
        self.assertEqual(f[1], 'high')
        (f,) = timeout_findings({'ISTIO_KUBE_HEADER_TIMEOUT': '90s'}, apiserver_request_timeout='2m')
        self.assertEqual(f[1], 'high')
        self.assertEqual([x[1] for x in timeout_findings({'ISTIO_KUBE_HEADER_TIMEOUT': '0', 'ISTIO_KUBE_REQUEST_TIMEOUT': '0'})], ['info', 'info'])
        with self.assertRaises(ValueError):
            timeout_findings({'ISTIO_KUBE_HEADER_TIMEOUT': 'ninety'})


if __name__ == '__main__':
    unittest.main()
