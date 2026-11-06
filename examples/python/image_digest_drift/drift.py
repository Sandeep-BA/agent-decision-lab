"""Find workloads whose pods run more than one image digest, from `kubectl get pods -o json` output.

Author: Sandeep Belgavi. Companion to "One Tag, Two Builds: Mutable Image Tags and imagePullPolicy on
Kubernetes" (aicassindra.com). Standard library only. Reads a JSON file or stdin; never contacts a cluster.
"""
import json
import sys
from collections import defaultdict


def owner(pod):
    """Group pods by their controller: the ReplicaSet name minus its hash suffix approximates the Deployment."""
    refs = pod['metadata'].get('ownerReferences') or [{'kind': 'Pod', 'name': pod['metadata']['name']}]
    ref = refs[0]
    name = ref['name']
    if ref['kind'] == 'ReplicaSet':
        name = name.rsplit('-', 1)[0]
    return pod['metadata'].get('namespace', 'default') + '/' + name


def report(pod_list):
    groups = defaultdict(lambda: defaultdict(list))
    for pod in pod_list['items']:
        specs = {c['name']: c for c in pod['spec']['containers']}
        for status in pod.get('status', {}).get('containerStatuses', []):
            spec = specs.get(status['name'], {})
            key = (owner(pod), status['name'], spec.get('image', status.get('image')), spec.get('imagePullPolicy'))
            digest = status.get('imageID') or 'not started'
            groups[key][digest].append(pod['metadata']['name'] + '@' + pod['spec'].get('nodeName', '?'))
    out = []
    for (workload, container, image, policy), digests in sorted(groups.items()):
        out.append({'workload': workload, 'container': container, 'image': image, 'pullPolicy': policy,
                    'pinned': '@sha256:' in (image or ''), 'digests': {d: sorted(p) for d, p in sorted(digests.items())},
                    'drift': len(digests) > 1})
    return out


if __name__ == '__main__':
    data = json.load(open(sys.argv[1], encoding='utf-8') if len(sys.argv) > 1 else sys.stdin)
    rows = report(data)
    for r in rows:
        print(json.dumps({'workload': r['workload'], 'pullPolicy': r['pullPolicy'], 'pinned': r['pinned'],
                          'digests': {d[-12:]: len(p) for d, p in r['digests'].items()}, 'drift': r['drift']}))
    sys.exit(1 if any(r['drift'] for r in rows) else 0)
