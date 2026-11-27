# Argo CD 3.6.3: A Create Request That Overwrites Must Pass the Update Permission

Author: **Sandeep Belgavi**.

Original teaching example for https://aicassindra.com/blogs/security/argo_cd_3_6_3_upsert_update_permission.html.

`example.py` is a behavioural model of the repository create handler described in GHSA-mfgm-4p7x-3ccr and fix commit 5b88885b40: before the fix a create with `upsert` replaced an existing, different repository after checking only `create`; after it, the request goes through the update handler. It shows that a replace clears omitted credentials, and audits a synthetic API table for other create-or-replace routes that do not require `update`.

Prerequisites: CPython 3.11 or newer (recorded with 3.13.5 on Windows 11). Standard library only; `requirements.txt` is intentionally empty and `.env.example` documents that nothing is read from the environment. No network, no credentials and no model call.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json`.

Limitations: not Argo CD code, and RBAC object matching (project and URL patterns) is reduced to a set of granted actions. Views are my own and do not represent any employer, past or present.
