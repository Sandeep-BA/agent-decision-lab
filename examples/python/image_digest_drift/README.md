# One tag, two builds: finding image digest drift

**Author: Sandeep Belgavi**

A runnable companion to *One Tag, Two Builds: Mutable Image Tags and imagePullPolicy on Kubernetes*
(aicassindra.com, Distributed systems). `drift.py` reads `kubectl get pods -o json` output, groups containers by
workload, and lists the digests they actually run from `status.containerStatuses[].imageID`. A workload with more
than one digest is reported as drift and the script exits with status 1, so it can run as a CI or cron check.

The fixture is synthetic: the fictional Belgavi's Book Store `recs` Deployment uses tag `recs:2.4`, six pods on
three old nodes run the old build and two pods on an autoscaled node run the re-pushed one; a `search`
Deployment pinned by digest runs one build.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- `.env.example` documents that nothing is read from the environment. The script never contacts a cluster; pipe
  `kubectl get pods -A -o json` into it yourself if you want a real report.

## Commands

```
python examples/python/image_digest_drift/drift.py examples/python/image_digest_drift/fixtures/pods.json
python -m unittest discover -s examples/python/image_digest_drift -p "test_*.py"
```

## Expected output

```
{"workload": "shop/recs", "pullPolicy": "IfNotPresent", "pinned": false, "digests": {"4f1a4f1a4f1a": 6, "9c7e9c7e9c7e": 2}, "drift": true}
{"workload": "shop/search", "pullPolicy": "IfNotPresent", "pinned": true, "digests": {"77aa77aa77aa": 3}, "drift": false}
```

The exit status is 1 because `shop/recs` drifts.

## Limitations

Workloads are grouped by the first owner reference, with the ReplicaSet hash suffix removed to approximate the
Deployment; StatefulSets, DaemonSets and Jobs are grouped by their own names. During a normal rollout two digests
are expected for a while, so alert only when drift lasts longer than your rollouts do. Init containers and
ephemeral containers are not inspected.
