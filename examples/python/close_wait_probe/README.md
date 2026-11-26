# Connections Stuck in CLOSE_WAIT Mean the Application Never Closed the Socket

Author: **Sandeep Belgavi**.

Original teaching example for https://aicassindra.com/blogs/networking/tcp_close_wait_unclosed_sockets.html.

- `example.py`: a keep-alive pool for a fictional Belgavi's Book Store stock service on 127.0.0.1. The service closes idle connections; the buggy pool keeps the half-closed sockets (20 after five bursts of four), the fixed pool detects peer close with a non-blocking `MSG_PEEK` and closes them (0). Portable: no netstat needed.
- `probe.py`: opens N loopback connections whose server side closes immediately and prints the TCP states reported by `netstat -ano -p tcp` (Windows syntax) before and after the client closes.

Prerequisites: CPython 3.11 or newer (tested with 3.13.5 on Windows 11). No third-party dependencies (`requirements.txt` is intentionally empty). `.env.example` documents that nothing is read from the environment. On Linux use `ss -tan state close-wait` instead of `probe.py`.

From this directory:

```text
python example.py
python -m unittest -v test_example.py
python probe.py 5
```

Expected output: `expected.json` for `example.py`; `probe-output-windows.txt` is one recorded probe run. netstat snapshots are not atomic, so a run can show transitional states and a TIME_WAIT count below N.

Limitations: loopback only; timings are short and chosen for tests. Views are my own and do not represent any employer, past or present.
