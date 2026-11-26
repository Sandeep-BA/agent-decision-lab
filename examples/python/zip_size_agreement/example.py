"""Author: Sandeep Belgavi. Companion to https://aicassindra.com/blogs/security/uv_0_13_10_zip_size_disagreement.html.
Defensive probe: a ZIP member with a data descriptor carries two compressed sizes.
Build a normal archive with a descriptor, understate the central-directory size, and compare a
central-directory reader (zipfile), a streaming reader that trusts the descriptor, and a strict check.
No CRC manipulation is performed; the understated member simply fails zipfile's CRC check.
"""
import io, struct, sys, zipfile, zlib


class Unseekable(io.RawIOBase):
    def __init__(self):
        self.buf = bytearray()
    def writable(self):
        return True
    def write(self, b):
        self.buf += b
        return len(b)


def build():
    sink = Unseekable()
    with zipfile.ZipFile(sink, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('pkg/__init__.py', "# synthetic module for Belgavi's Book Store\nVALUE = 1\nprint('line two of the module')\n" * 3)
    return bytes(sink.buf)


def central_entries(data):
    eocd = data.rfind(b'PK\x05\x06')
    count, size, offset = struct.unpack('<HII', data[eocd + 10:eocd + 20])
    out, p = [], offset
    for _ in range(count):
        assert data[p:p + 4] == b'PK\x01\x02'
        flags, method = struct.unpack_from('<HH', data, p + 8)
        crc, csize, usize = struct.unpack_from('<III', data, p + 16)
        nlen, elen, clen = struct.unpack_from('<HHH', data, p + 28)
        lho = struct.unpack_from('<I', data, p + 42)[0]
        name = data[p + 46:p + 46 + nlen].decode()
        out.append({'name': name, 'flags': flags, 'crc': crc, 'csize': csize, 'usize': usize, 'cd_pos': p, 'lho': lho})
        p += 46 + nlen + elen + clen
    return out


def streaming_read(data, lho):
    """Read from the local header to the end of the deflate stream, then read the descriptor."""
    nlen, elen = struct.unpack('<HH', data[lho + 26:lho + 30])
    start = lho + 30 + nlen + elen
    d = zlib.decompressobj(-15)
    out = d.decompress(data[start:])
    consumed = len(data[start:]) - len(d.unused_data)
    desc = data[start + consumed:start + consumed + 16]
    if desc[:4] == b'PK\x07\x08':
        desc = desc[4:]
    crc, csize, usize = struct.unpack('<III', desc[:12])
    return out, consumed, crc, csize, usize


def check_members(data: bytes):
    """Defensive check in the spirit of uv 0.13.10: for each deflated member with a data descriptor,
    the bytes a streaming reader consumes, the descriptor size and the central-directory size must agree."""
    problems = []
    for e in central_entries(data):
        if not e["flags"] & 8:
            continue
        _, consumed, _, dcsize, _ = streaming_read(data, e["lho"])
        if not (consumed == dcsize == e["csize"]):
            problems.append({"name": e["name"], "consumed": consumed, "descriptor": dcsize, "central": e["csize"]})
    return problems


def understate(data: bytes, new_size: int = 29) -> bytes:
    out = bytearray(data)
    e = central_entries(data)[0]
    struct.pack_into('<I', out, e['cd_pos'] + 20, new_size)
    return bytes(out)


def main():
    data = bytearray(build())
    e = central_entries(bytes(data))[0]
    print('python', sys.version.split()[0])
    print('flags bit 3 (data descriptor):', bool(e['flags'] & 8), 'central csize:', e['csize'], 'usize:', e['usize'])
    body, consumed, dcrc, dcsize, dusize = streaming_read(bytes(data), e['lho'])
    print('streaming reader: consumed', consumed, 'descriptor csize', dcsize, 'bytes out', len(body))
    # Understate the central-directory compressed size (offset 20 within the central header).
    short = 29
    struct.pack_into('<I', data, e['cd_pos'] + 20, short)
    e2 = central_entries(bytes(data))[0]
    print('patched central csize:', e2['csize'])
    try:
        zipfile.ZipFile(io.BytesIO(bytes(data))).read('pkg/__init__.py')
        print('zipfile: read succeeded')
    except Exception as ex:
        print('zipfile:', type(ex).__name__, '-', ex)
    body2, consumed2, _, dcsize2, _ = streaming_read(bytes(data), e2['lho'])
    print('streaming reader after patch: consumed', consumed2, 'bytes out', len(body2), 'descriptor csize', dcsize2)
    print('strict check (descriptor == central == consumed):', dcsize2 == e2['csize'] == consumed2)
    print('check_members(original):', check_members(build()))
    print('check_members(patched):', check_members(bytes(data)))


if __name__ == '__main__':
    main()
