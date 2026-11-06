# HTTP request framing: two parsers that disagree and one that does not

**Author: Sandeep Belgavi**

A runnable companion to *HTTP Request Smuggling: When a Proxy and a Backend Disagree About Where a Request Ends*
(aicassindra.com, Security). `framing.py` contains two lenient toy framers, one that trusts `Content-Length` and
one that honours `Transfer-Encoding: chunked`, and shows that fed the CL.TE probe from the article they disagree
by one byte, so the next request on the connection begins with `G`. A strict framer implements the RFC 9112
section 6 rules the article tabulates and refuses the probe.

**Pure functions over bytes.** Nothing opens a socket. Test real proxies and servers only on systems you own or
are authorised to test.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- `.env.example` documents that nothing is read from the environment.

## Commands

```
python examples/python/http_framing_toy/framing.py
python -m unittest discover -s examples/python/http_framing_toy -p "test_*.py"
```

## Expected output

```
{"front_cl_back_te_next_request_line": "GPOST /checkout HTTP/1.1"}
{"strict": "400: both Transfer-Encoding and Content-Length; close the connection"}
```

## Limitations

The framers handle request lines, headers, `Content-Length` and minimal chunked bodies only: no chunk extensions,
trailers, obsolete line folding, pipelining edge cases or HTTP/2. Rejecting both headers together is the
conservative reading of the RFC's MAY; refusing codings other than plain chunked is a local policy for a backend
that implements nothing else.
