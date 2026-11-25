# Work Out Kubernetes Topology Spread maxSkew Before a Zone Goes Down

Author: **Sandeep Belgavi**.

Original synthetic teaching example for https://aicassindra.com/blogs/distributed/kubernetes_topology_spread_max_skew.html (article publication pending).

Prerequisites: CPython 3.13 (tested with 3.13.5). No third-party runtime dependencies.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

`expected.json` records the demonstration output of a successful local run. Tests cover failure boundaries and invariants; see the test file for each fixture.

Limitations: A model of the documented topology spread rules, not the kube-scheduler. It ignores node-level placement, affinity, nodeAffinityPolicy, per-pod tolerations, terminating-pod accounting and scoring weights. Manifests in the guide were not applied to a cluster. No model, SDK or provider is contacted. Views are my own and do not represent any employer, past or present.
