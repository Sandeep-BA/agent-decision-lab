# uv 0.13.10 Rejects ZIP Members Whose Two Compressed Sizes Disagree

Author: **Sandeep Belgavi**.

Original defensive teaching example for https://aicassindra.com/blogs/security/uv_0_13_10_zip_size_disagreement.html.

It writes a small synthetic wheel-like archive with Python's `zipfile` to an unseekable stream, so the member uses a data descriptor, then understates the compressed size recorded in the central directory. Python's `zipfile`, which reads the central-directory size, rejects the member with `Bad CRC-32`; a minimal streaming reader that inflates to the end of the deflate stream and reads the descriptor extracts the full file. `check_members()` reports any deflated descriptor member whose consumed bytes, descriptor size and central-directory size disagree, which is the condition uv 0.13.10 now rejects (GHSA-vjvj-3m3f-fgmm).

Prerequisites: CPython 3.11 or newer (tested with 3.13.5). No third-party dependencies (`requirements.txt` is intentionally empty). `.env.example` documents that nothing is read from the environment.

```text
python example.py
python -m unittest -v test_example.py
```

Expected output: `expected.txt` (first line, the Python version, omitted).

Limitations: only the CRC-mismatch case is shown; no CRC manipulation or collision construction is included. The streaming reader is a minimal teaching reader for deflated members, not uv's extractor and not a complete ZIP implementation. Upgrade uv rather than relying on this check. Views are my own and do not represent any employer, past or present.
