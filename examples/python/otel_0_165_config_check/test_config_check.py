"""Author: Sandeep Belgavi."""
import copy
import unittest
from config_check import SAMPLE, review


class Review(unittest.TestCase):
    def test_sample_findings(self):
        findings = review(SAMPLE)
        self.assertIn(('warn', 'exporters.otlp_http/books.max_idle_conns', 'move to keepalive.max_idle_conns'), findings)
        self.assertIn(('warn', 'exporters.otlp_http/books.idle_conn_timeout', 'move to keepalive.idle_conn_timeout'), findings)
        self.assertIn(('warn', 'service.pipelines.traces', 'batch processor and otlp_http/books sending_queue batching both enabled'), findings)
        self.assertEqual(len(findings), 3)

    def test_fixed_config_is_clean(self):
        cfg = copy.deepcopy(SAMPLE)
        ex = cfg['exporters']['otlp_http/books']
        ex.pop('max_idle_conns'); ex.pop('idle_conn_timeout')
        ex['keepalive'] = {'max_idle_conns': 50, 'idle_conn_timeout': '60s'}
        cfg['service']['pipelines']['traces']['processors'] = ['memory_limiter']
        self.assertEqual(review(cfg), [])

    def test_disabled_queue_does_not_double_batch(self):
        cfg = copy.deepcopy(SAMPLE)
        cfg['exporters']['otlp_http/books']['sending_queue']['enabled'] = False
        self.assertFalse(any('both enabled' in f[2] for f in review(cfg)))

    def test_signalfx_receiver_and_disable_keep_alives(self):
        cfg = {'receivers': {'signalfx/legacy': {}}, 'exporters': {'otlp_http': {'disable_keep_alives': True}}}
        self.assertEqual(review(cfg), [
            ('warn', 'exporters.otlp_http.disable_keep_alives', 'move to keepalive.enabled: false'),
            ('high', 'receivers.signalfx/legacy', 'SignalFx receiver removed from contrib in 0.165.0; use OTLP'),
        ])


if __name__ == '__main__':
    unittest.main()
