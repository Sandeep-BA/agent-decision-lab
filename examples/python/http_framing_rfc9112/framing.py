"""HTTP/1.1 request framing per RFC 9112 section 6, and why disagreement smuggles. Author: Sandeep Belgavi.

`frame()` decides how long a request body is, or rejects the request, following
RFC 9112 6.1 and 6.3 for requests: Transfer-Encoding with chunked not final is
a 400; both Transfer-Encoding and Content-Length is handled as an error in
strict mode (6.3 says it "ought to be handled as an error"), or, in forwarding
mode, Content-Length is removed and chunked framing used, as 6.3 requires of an
intermediary that forwards it; an invalid Content-Length is a 400 unless it is a
list of identical valid values; Transfer-Encoding in an HTTP/1.0 request is
faulty framing. `split_stream()` shows two lenient parsers that each pick one
header reading the same bytes and disagreeing about where the next request
starts. Synthetic bytes only; nothing is sent over a network.
"""
from __future__ import annotations

import json
import re

DIGITS = re.compile(r'^[0-9]+$')


class Reject(Exception):
    def __init__(self, status: int, reason: str):
        super().__init__(f'{status} {reason}')
        self.status, self.reason = status, reason


def parse_head(raw: bytes) -> tuple[str, list[tuple[str, str]], bytes]:
    head, sep, rest = raw.partition(b'\r\n\r\n')
    if not sep:
        raise Reject(400, 'incomplete header section')
    lines = head.decode('latin-1').split('\r\n')
    fields = []
    for line in lines[1:]:
        name, colon, value = line.partition(':')
        if not colon or name != name.strip() or not name:
            raise Reject(400, f'malformed field line {line!r}')   # includes whitespace before the colon
        fields.append((name.lower(), value.strip()))
    return lines[0], fields, rest


def frame(raw: bytes, mode: str = 'strict') -> dict:
    request_line, fields, rest = parse_head(raw)
    version = request_line.rsplit(' ', 1)[-1]
    te = [v for n, v in fields if n == 'transfer-encoding']
    cl = [v for n, v in fields if n == 'content-length']
    if te:
        if version == 'HTTP/1.0':
            raise Reject(400, 'Transfer-Encoding in an HTTP/1.0 message: faulty framing, close after')
        codings = [c.strip().lower() for v in te for c in v.split(',') if c.strip()]
        if not codings or codings[-1] != 'chunked':
            raise Reject(400, 'chunked is not the final transfer coding')
        if cl:
            if mode == 'strict':
                raise Reject(400, 'both Transfer-Encoding and Content-Length')
            fields = [(n, v) for n, v in fields if n != 'content-length']
        body, leftover = read_chunked(rest)
        return {'framing': 'chunked', 'body': body.decode('latin-1'), 'leftover': leftover.decode('latin-1'),
                'removed_content_length': bool(cl)}
    if cl:
        values = [p.strip() for v in cl for p in v.split(',')]
        if not all(DIGITS.match(p) for p in values) or len(set(int(p) for p in values)) != 1:
            raise Reject(400, f'invalid Content-Length {cl}')
        n = int(values[0])
        if len(rest) < n:
            raise Reject(400, 'body shorter than Content-Length: incomplete, close')
        return {'framing': 'content-length', 'body': rest[:n].decode('latin-1'), 'leftover': rest[n:].decode('latin-1'),
                'removed_content_length': False}
    return {'framing': 'none', 'body': '', 'leftover': rest.decode('latin-1'), 'removed_content_length': False}


def read_chunked(data: bytes) -> tuple[bytes, bytes]:
    body, pos = b'', 0
    while True:
        eol = data.find(b'\r\n', pos)
        if eol < 0:
            raise Reject(400, 'incomplete chunk size line')
        size_text = data[pos:eol].split(b';', 1)[0].strip()
        if not re.fullmatch(rb'[0-9A-Fa-f]+', size_text):
            raise Reject(400, f'invalid chunk size {size_text!r}')
        size, pos = int(size_text, 16), eol + 2
        if size == 0:
            end = data.find(b'\r\n', pos)           # no trailers in this model: expect the final CRLF
            if end != pos:
                raise Reject(400, 'trailer section not supported by this model')
            return body, data[pos + 2:]
        if len(data) < pos + size + 2 or data[pos + size:pos + size + 2] != b'\r\n':
            raise Reject(400, 'chunk data does not end with CRLF')
        body += data[pos:pos + size]
        pos += size + 2


def lenient(raw: bytes, prefer: str) -> dict:
    """A parser that silently prefers one header, as the two halves of a smuggling pair do."""
    _, fields, rest = parse_head(raw)
    names = {n for n, _ in fields}
    if prefer == 'content-length' and 'content-length' in names:
        n = int(next(v for k, v in fields if k == 'content-length'))
        return {'body': rest[:n].decode('latin-1'), 'leftover': rest[n:].decode('latin-1')}
    body, leftover = read_chunked(rest)
    return {'body': body.decode('latin-1'), 'leftover': leftover.decode('latin-1')}


# One request with both headers. Content-Length (56) counts every byte after the
# head: the zero chunk plus a whole second request. Chunked framing ends at the
# zero chunk, so a chunked reader leaves the second request in the stream.
SMUGGLE = (b'POST /returns HTTP/1.1\r\nHost: shop.example\r\nContent-Length: 56\r\nTransfer-Encoding: chunked\r\n\r\n'
           b'0\r\n\r\nGET /admin/refunds HTTP/1.1\r\nHost: shop.example\r\n\r\n')
CASES = {
    'content-length only': b'POST /returns HTTP/1.1\r\nHost: shop.example\r\nContent-Length: 9\r\n\r\nCASE-6201',
    'chunked only': b'POST /returns HTTP/1.1\r\nHost: shop.example\r\nTransfer-Encoding: chunked\r\n\r\n9\r\nCASE-6201\r\n0\r\n\r\n',
    'both headers': SMUGGLE,
    'gzip after chunked': b'POST /returns HTTP/1.1\r\nHost: shop.example\r\nTransfer-Encoding: chunked, gzip\r\n\r\n',
    'duplicate equal lengths': b'POST /returns HTTP/1.1\r\nHost: shop.example\r\nContent-Length: 9, 9\r\n\r\nCASE-6201',
    'conflicting lengths': b'POST /returns HTTP/1.1\r\nHost: shop.example\r\nContent-Length: 9\r\nContent-Length: 10\r\n\r\nCASE-6201',
    'signed length': b'POST /returns HTTP/1.1\r\nHost: shop.example\r\nContent-Length: +9\r\n\r\nCASE-6201',
    'space before colon': b'POST /returns HTTP/1.1\r\nHost: shop.example\r\nTransfer-Encoding : chunked\r\n\r\n0\r\n\r\n',
    'TE in HTTP/1.0': b'POST /returns HTTP/1.0\r\nHost: shop.example\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n',
}


def run() -> dict:
    table = {}
    for name, raw in CASES.items():
        row = {}
        for mode in ('strict', 'forward'):
            try:
                r = frame(raw, mode)
                row[mode] = f"{r['framing']} body={r['body']!r} leftover={len(r['leftover'])}B"
            except Reject as e:
                row[mode] = f'reject {e.status}: {e.reason}'
        table[name] = row
    front, back = lenient(SMUGGLE, 'content-length'), lenient(SMUGGLE, 'chunked')
    return {'framing': table,
            'desync': {'front_end_uses_content_length': {'body_bytes': len(front['body']), 'leftover': front['leftover']},
                       'back_end_uses_chunked': {'body_bytes': len(back['body']), 'leftover_starts': back['leftover'].split('\r\n')[0]}}}


if __name__ == '__main__':
    print(json.dumps(run(), indent=1))
