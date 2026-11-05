# Replaying Pod outcomes against a Job spec: backoffLimit and podFailurePolicy

**Author: Sandeep Belgavi**

A runnable companion to *Kubernetes Jobs That Retry the Wrong Failures: backoffLimit and podFailurePolicy*
(aicassindra.com, Distributed systems). It replays scripted Pod outcomes for the fictional Belgavi's Book Store
catalogue import against a Job spec and reports how many failures were counted, how many Pods ran and why the
Job ended.

**No cluster is used.** This is a model of the rules in the Kubernetes Jobs documentation and the Job v1 API
reference: rules in order with the first match winning, FailJob, Ignore and Count, exit-code rules with `In` and
`NotIn`, Pod-condition rules on type and status, backoffLimit as the number of retries, and
activeDeadlineSeconds. It checks two API validation rules: value 0 with `In`, and exactly one matcher per rule.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- No network, no kubeconfig and no API key. `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/job_failure_policy/jobpolicy.py examples/python/job_failure_policy/fixtures/nights.json
python -m unittest discover -s examples/python/job_failure_policy -p "test_*.py"
```

## Expected output

`expected_output.json` holds every case. Pods run 120 s and evictions happen at 60 s.

| Case | Result | Pods | Counted failures | Ends at (s) |
| --- | --- | --- | --- | --- |
| Default, backoffLimit 6 (drain, drain, crash, success) | succeeded | 4 | 3 | 430 |
| Default, backoffLimit 2 | failed, BackoffLimitExceeded | 3 | 3 | 270 |
| Article policy, backoffLimit 3 | succeeded | 4 | 1 | 370 |
| Article policy, malformed feed (exit 3) | failed, FailJob rule | 1 | 0 | 120 |
| Default, malformed feed | failed, 630 s of back-off | 7 | 7 | 1,470 |
| Article policy, OOM (exit 137) every time | failed | 4 | 4 | 550 |
| Article policy, node-pressure evictions | still active after 100 Pods | 100 | 0 | 6,000 |
| Same, activeDeadlineSeconds 3600 | failed, DeadlineExceeded | 60 | 0 | 3,600 |

## Limitations

Timing is simplified: Pods start instantly, the back-off delay applies only after counted failures, and the
controller is assumed to observe each failure at once. Indexed Jobs, backoffLimitPerIndex, FailIndex and
maxFailedIndexes, podReplacementPolicy, terminating-Pod accounting and successPolicy are not modelled. Confirm
behaviour against a real cluster before relying on a policy; the article describes a three-run test with
`kubectl drain`.
