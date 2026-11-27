# Work Out When a Kubernetes HPA Will Scale Down: Tolerance, Stabilization Window and Rate Policies

Author: **Sandeep Belgavi**.

Original teaching example for https://aicassindra.com/blogs/distributed/kubernetes_hpa_scale_down_behavior.html.

`example.py` replays an autoscaling/v2 HorizontalPodAutoscaler every 15 seconds following the Kubernetes v1.37.3 controller functions for the usage ratio and tolerance, the stabilization window and the scale-up and scale-down rate policies. A synthetic workload falls from 1200 to 300 pod-percent of CPU at t=0 with a 60 percent target.

Prerequisites: CPython 3.11 or newer (recorded with 3.13.5 on Windows 11). Standard library only; `requirements.txt` is intentionally empty and `.env.example` documents that nothing is read from the environment. No network, no credentials and no model call.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json` (defaults hold 20 replicas until 285 s and then drop to 5; two-pods-per-minute reaches 5 at 465 s; 25-percent-per-minute at 345 s; 64 percent against a 60 percent target stays inside the default tolerance).

Limitations: a calculation, not a cluster run. Pod readiness, missing metrics, CPU initialization and metric delay are omitted, and real sync times drift, so treat the seconds as approximate. Views are my own and do not represent any employer, past or present.
