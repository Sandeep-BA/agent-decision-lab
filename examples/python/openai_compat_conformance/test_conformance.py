"""Author: Sandeep Belgavi. Offline tests: the suite against the fake server's two profiles."""
import json
import os
import unittest

import conformance
import fake_server

HERE = os.path.dirname(os.path.abspath(__file__))


def verdicts(results):
    return {r['check']: r['verdict'] for r in results}


class ConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strict, strict_url = fake_server.serve('strict')
        cls.lenient, lenient_url = fake_server.serve('lenient')
        cls.strict_v = verdicts(conformance.run(strict_url, 'fake'))
        cls.lenient_v = verdicts(conformance.run(lenient_url, 'fake'))

    @classmethod
    def tearDownClass(cls):
        cls.strict.shutdown()
        cls.lenient.shutdown()

    def test_strict_profile_passes_everything(self):
        self.assertEqual(set(self.strict_v.values()), {'PASS'}, self.strict_v)

    def test_lenient_profile_reproduces_the_recorded_diffs(self):
        diffs = sorted(k for k, v in self.lenient_v.items() if v != 'PASS')
        self.assertEqual(diffs, ['max_completion_tokens', 'n', 'seed', 'unknown_param'])

    def test_recorded_ollama_run_matches_the_lenient_profile(self):
        path = os.path.join(HERE, 'fixtures', 'ollama-0.40.6-qwen2.5-0.5b-2026-10-25.json')
        with open(path, encoding='utf-8') as f:
            recorded = verdicts(json.load(f))
        self.assertEqual(recorded, self.lenient_v)

    def test_every_check_reports_a_verdict(self):
        self.assertEqual(len(self.strict_v), len(conformance.CHECKS))

    def test_unreachable_server_fails_instead_of_passing(self):
        results = verdicts(conformance.run('http://127.0.0.1:9/v1', 'fake'))
        self.assertNotIn('PASS', set(results.values()))


if __name__ == '__main__':
    unittest.main()
