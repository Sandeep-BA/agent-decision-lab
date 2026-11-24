# A Reused Process ID Must Not Authorize Worker Cleanup

Author: **Sandeep Belgavi**. Original explanation, code and synthetic fixtures.

Separate a numeric process locator from an owned process incarnation and demonstrate a safe refusal after reuse.

Article destination (publication pending): https://aicassindra.com/blogs/system_design/background_worker_pid_reuse_identity.html

## Prerequisites

CPython 3.13.5. No third-party dependencies; requirements.txt intentionally contains no packages.

## Run from this directory

```text
python example.py
python -m unittest test_example -v
```

Input: `sample-input.json`. Expected output: `expected-output.json`. Tests include negative outcomes, state preservation and boundary cases. All fixtures are synthetic; no provider call occurs.

## Limits

Advisory record comparison only. No process queries or termination. It does not close the check-to-action race; a real adapter needs a platform-bound identity.

Views are my own and do not represent any employer, past or present.

## Primary references

- [Claude Code v2.1.326 release notes, 16 November 2026 UTC](https://github.com/anthropics/claude-code/releases/tag/v2.1.326)
- [Java SE 25 ProcessHandle: process identity and PID reuse](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ProcessHandle.html)
