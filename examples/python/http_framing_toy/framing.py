"""Two lenient HTTP/1.1 request framers that disagree, and a strict one that follows RFC 9112 section 6.

Author: Sandeep Belgavi. Companion to "HTTP Request Smuggling: When a Proxy and a Backend Disagree About Where a
Request Ends" (aicassindra.com). Standard library only. Pure functions over bytes: no sockets, no network.
These toys exist to show the disagreement and to test a framing rule; they are not an HTTP implementation.
"""
CRLF = b'\r\n'


class Reject(Exception):
    pass


def split_head(buf):
    head, sep, rest = buf.partition(CRLF + CRLF)
    if not sep:
        raise Reject('incomplete header section')
    lines = head.split(CRLF)
    headers = []
    for line in lines[1:]:
        name, _, value = line.decode('latin-1').partition(':')
        headers.append((name, value))
    return lines[0].decode('latin-1'), headers, rest


def read_chunked(body):
    """Return (consumed, decoded). Minimal chunked decoder: hex size lines, no extensions, no trailers."""
    pos, out = 0, b''
    while True:
        end = body.index(CRLF, pos)
        size = int(body[pos:end], 16)
        pos = end + 2
        if size == 0:
            if body[pos:pos + 2] != CRLF:
                raise Reject('missing final CRLF')
            return pos + 2, out
        out += body[pos:pos + size]
        pos += size + 2


def lenient_cl_first(buf):
    """A front end that trusts Content-Length when present and ignores Transfer-Encoding."""
    line, headers, rest = split_head(buf)
    h = {n.strip().lower(): v.strip() for n, v in headers}
    n = int(h.get('content-length', '0'))
    return line, rest[:n], rest[n:]


def lenient_te_first(buf):
    """A back end that honours chunked whenever Transfer-Encoding mentions it."""
    line, headers, rest = split_head(buf)
    h = {n.strip().lower(): v.strip().lower() for n, v in headers}
    if 'chunked' in h.get('transfer-encoding', ''):
        used, body = read_chunked(rest)
        return line, body, rest[used:]
    n = int(h.get('content-length', '0'))
    return line, rest[:n], rest[n:]


def body_length_rule(headers):
    """headers: list of (name, value) as received. Returns ('chunked', None) or ('length', n)."""
    names = [n for n, _ in headers]
    if any(n != n.strip() for n in names):
        raise Reject('400: whitespace around a field name')
    lower = [(n.lower(), v.strip()) for n, v in headers]
    te = [v.lower() for n, v in lower if n == 'transfer-encoding']
    cl = [v for n, v in lower if n == 'content-length']
    if te and cl:
        raise Reject('400: both Transfer-Encoding and Content-Length; close the connection')
    if te:
        codings = [c.strip() for v in te for c in v.split(',')]
        if codings[-1] != 'chunked':
            raise Reject('400: chunked is not the final transfer coding')
        if codings != ['chunked']:
            raise Reject('501: transfer coding not implemented')
        return ('chunked', None)
    values = {c.strip() for v in cl for c in v.split(',')}
    if not values:
        return ('length', 0)
    value = values.pop() if len(values) == 1 else ''
    if not (value.isascii() and value.isdigit()):
        raise Reject('400: invalid or conflicting Content-Length')
    return ('length', int(value))


def strict(buf):
    line, headers, rest = split_head(buf)
    kind, n = body_length_rule(headers)
    if kind == 'chunked':
        used, body = read_chunked(rest)
        return line, body, rest[used:]
    return line, rest[:n], rest[n:]


PROBE = (b'POST /search HTTP/1.1\r\nHost: shop.example\r\nContent-Length: 6\r\nTransfer-Encoding: chunked\r\n\r\n'
         b'0\r\n\r\nG')
NEXT = b'POST /checkout HTTP/1.1\r\nHost: shop.example\r\nContent-Length: 0\r\n\r\n'


def desync(front, back, stream):
    """Front end forwards what it framed; the back end frames the same bytes plus the next request."""
    line, body, leftover = front(stream)
    forwarded = stream[:len(stream) - len(leftover)]
    _, _, back_left = back(forwarded + NEXT)
    return back_left.split(CRLF, 1)[0].decode('latin-1')


if __name__ == '__main__':
    import json
    print(json.dumps({'front_cl_back_te_next_request_line': desync(lenient_cl_first, lenient_te_first, PROBE)}))
    try:
        strict(PROBE)
    except Reject as e:
        print(json.dumps({'strict': str(e)}))
