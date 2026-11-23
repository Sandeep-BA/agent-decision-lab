# TCP retransmission timeout per RFC 6298

**Author: Sandeep Belgavi**

A runnable companion to *How TCP Computes Its Retransmission Timeout: SRTT, RTTVAR, Karn and Backoff* (aicassindra.com). Implements the RFC 6298 estimator (SRTT, RTTVAR, K = 4, granularity G, 1 s floor, maximum of at least 60 s), exponential backoff, the 3 s rule after a lost SYN and Karn's rule, and traces it over synthetic RTT series.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

`SERIES`: eight 100 ms samples, a spike of 400/420/380 ms, six 100 ms samples. `SERIES_LONG`: the same shape at 300/900 ms.

## Commands

From this directory:

```
python rto.py
python -m unittest -v
```

## Expected output

With the 1 s floor the short path stays at 1.0 s throughout. With a 0.2 s floor the RTO rises to 0.798 s at the spike. Long path peaks at 1.703 s. Backoff from 1 s: 1, 2, 4, 8, 16, 32, 60, 60. Karn: the careful estimator keeps the backed-off 0.6 s; the naive one drops to 0.419 s. 7 tests pass.

## Limitations

Estimator only: no congestion control, no timestamps option (RFC 7323) beyond a flag, no real sockets. The 0.2 s floor is for illustration; RFC 6298 recommends 1 s.

Views are my own and do not represent any employer, past or present.
