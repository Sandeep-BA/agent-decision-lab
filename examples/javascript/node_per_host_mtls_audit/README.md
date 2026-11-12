# Triage for the Node.js 11 November 2026 per-host mTLS fixes

**Author: Sandeep Belgavi**

A runnable companion to *Node.js 11 November 2026 Security Releases: Per-Host mTLS, SNI Changes and TLS Session Reuse* (aicassindra.com). An offline audit: the running version against v22.23.5, v24.22.3 and v26.13.1, the https.Agent key collision behind CVE-2026-123877, and findings for CA-only SNI contexts and mixed client-CA policies on one listener.

## Prerequisites

- Node.js 22, 24 or 26. No dependencies (`package.json` pins none). No network, no server started.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

A declarative server description in audit.mjs with a CA-only admin context.

## Commands

From this directory:

```
node --test
node audit.mjs
```

## Expected output

Five tests pass. On Node.js 22.17.0 the audit reports "vulnerable", identical agent keys for omitted ca and ca: [], and findings for CVE-2026-123867 and CVE-2026-123872.

## Limitations

Checks configuration you describe, not live traffic, and was not run on a patched binary. It does not test the HTTP/2 fixes in the same release.

Views are my own and do not represent any employer, past or present.
