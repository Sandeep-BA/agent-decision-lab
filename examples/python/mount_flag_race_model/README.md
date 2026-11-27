# Docker 29.10.1 Closes a docker cp Race That Left Read-Only Bind Mounts Writable

Author: **Sandeep Belgavi**.

Original teaching example for https://aicassindra.com/blogs/security/docker_29_10_1_cp_readonly_bind_race.html.

`example.py` is an in-memory model of the mount setup order described in GHSA-vfmq-r373-x89f and moby/moby PR 54279. A container process renames two directories between any two daemon steps. In the old order the read-only flag is applied through a path read back from the descriptor and resolved again; in the new order the mount is finished in a daemon-private staging directory and moved onto the descriptor.

Prerequisites: CPython 3.11 or newer (recorded with 3.13.5 on Windows 11). Standard library only; `requirements.txt` is intentionally empty and `.env.example` documents that nothing is read from the environment. No network, no credentials and no model call.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.json` (old order: the read-only source stays writable when the swap lands between the readlink and the remount; new order: safe at every interleaving).

Limitations: models ordering only. It does not call mount(2), does not reproduce the vulnerability and is not a Docker test. Views are my own and do not represent any employer, past or present.
