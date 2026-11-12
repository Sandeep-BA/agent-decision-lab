# An approval broker where prompts have a lifecycle

**Author: Sandeep Belgavi**

A runnable companion to *Approval Prompts Have a Lifecycle: Withdrawal, Per-Endpoint Queues and Deny Instead of Prompting* (aicassindra.com). Per-endpoint prompt queues, withdrawal when a request ends, decisions bound to a live prompt and its originating turn, session grants and denies, and an unattended mode that denies instead of prompting.

## Prerequisites

- Python 3.11 or newer. Standard library only. No coding agent, no network.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

`demo()` submits three requests to registry.npmjs.org and one to catalog.example.test in turn t1.

## Commands

From this directory:

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Seven tests pass. Two prompts are shown for four requests; a late decision on a withdrawn prompt is rejected and creates no session grant; unattended mode denies all four and shows none.

## Limitations

Original model based on public release notes and pull request descriptions; it is not the implementation of Codex CLI or Claude Code.

Views are my own and do not represent any employer, past or present.
