"""Tests for the image digest drift report. Author: Sandeep Belgavi."""
import copy
import json
import pathlib
import unittest

import drift

HERE = pathlib.Path(__file__).resolve().parent
PODS = json.loads((HERE / 'fixtures' / 'pods.json').read_text(encoding='utf-8'))


class Report(unittest.TestCase):
    def test_tagged_deployment_runs_two_builds(self):
        r = {x['workload']: x for x in drift.report(PODS)}['shop/recs']
        self.assertTrue(r['drift'])
        self.assertEqual(sorted(len(p) for p in r['digests'].values()), [2, 6])
        self.assertFalse(r['pinned'])

    def test_digest_pinned_deployment_has_one_build(self):
        r = {x['workload']: x for x in drift.report(PODS)}['shop/search']
        self.assertEqual((r['drift'], r['pinned'], len(r['digests'])), (False, True, 1))

    def test_pod_stuck_before_start_is_its_own_group(self):
        pods = copy.deepcopy(PODS)
        pods['items'][0]['status']['containerStatuses'][0].pop('imageID')
        r = {x['workload']: x for x in drift.report(pods)}['shop/recs']
        self.assertIn('not started', r['digests'])

    def test_new_pods_are_on_the_new_node(self):
        r = {x['workload']: x for x in drift.report(PODS)}['shop/recs']
        newest = [d for d, p in r['digests'].items() if len(p) == 2][0]
        self.assertTrue(all(name.endswith('@node-new') for name in r['digests'][newest]))


if __name__ == '__main__':
    unittest.main()
