# HTTP/1.1 request framing per RFC 9112

**Author: Sandeep Belgavi**

A runnable companion to *Reject Ambiguous HTTP/1.1 Framing Before a Proxy and a Server Disagree* (aicassindra.com). A small framing decision function following RFC 9112 sections 6.1 and 6.3 (Transfer-Encoding with chunked last, Content-Length validation, both headers present, HTTP/1.0 with Transfer-Encoding) and two lenient parsers that read one byte stream differently.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13 on Windows). Standard library only; `requirements.txt` lists nothing to install.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

Nine synthetic requests in `framing.py`, including one with both Content-Length: 56 and Transfer-Encoding: chunked whose body hides a second request.

## Commands

From this directory:

```
python framing.py
python -m unittest -v
```

## Expected output

Strict mode rejects both-headers, chunked-not-final, conflicting or signed lengths, whitespace before the colon and TE in HTTP/1.0. Forward mode drops Content-Length and frames by chunked, leaving 51 bytes as the next request. The lenient pair: the Content-Length reader takes all 56 bytes, the chunked reader leaves `GET /admin/refunds HTTP/1.1` in the stream. 8 tests pass.

## Limitations

Requests only, no trailers, no obs-fold, no response framing and no sockets. Not a hardened parser; use your proxy's and server's own strict settings.

Views are my own and do not represent any employer, past or present.
