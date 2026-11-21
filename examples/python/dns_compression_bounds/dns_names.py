"""Bounded decoding of compressed DNS names (RFC 1035 4.1.4, RFC 9267). Author: Sandeep Belgavi.

Every packet here is synthetic and built in this file under example.com
(reserved for documentation by RFC 2606). Nothing is sent on a network.

decode_name() returns the dotted name, the wire offset where the caller's
next field starts, and a trace. It refuses: reads past the end, labels with
the reserved 01/10 prefixes, pointers into the 12-octet header, pointers that
do not point strictly backward (when backward_only is on), more than
max_hops pointers, and names longer than 255 octets on the wire.
"""
import json
import sys

HEADER = bytes([0x1a, 0x2b, 0x81, 0x80, 0, 1, 0, 1, 0, 0, 0, 0])
SAFETY_CAP = 10_000


class NameError_(ValueError):
    pass


def label(text):
    raw = text.encode('ascii')
    return bytes([len(raw)]) + raw


def name(*labels):
    return b''.join(label(x) for x in labels) + b'\x00'


def build_fixtures():
    q = name('books', 'example', 'com')               # at offset 12, 19 octets
    valid = HEADER + q + b'\x00\x01\x00\x01' + label('help') + b'\xc0\x0c' + b'\x00\x01\x00\x01'
    long_ = bytearray(HEADER)
    starts = []
    for i in range(4):
        starts.append(len(long_))
        long_ += bytes([63]) + bytes([ord('a') + i]) * 63
        long_ += b'\x00' if i == 0 else bytes([0xc0, starts[i - 1]])
    return {
        'valid': {'packet': valid, 'offset': 35, 'note': 'help + pointer to books.example.com at 12'},
        'self_loop': {'packet': HEADER + b'\xc0\x0c', 'offset': 12, 'note': 'pointer at 12 targets 12'},
        'two_pointer_loop': {'packet': HEADER + b'\xc0\x0e\xc0\x0c', 'offset': 12, 'note': '12 -> 14 -> 12'},
        'forward_pointer': {'packet': HEADER + b'\xc0\x0e' + name('com'), 'offset': 12, 'note': 'pointer to a later, valid name'},
        'header_pointer': {'packet': HEADER + b'\xc0\x02', 'offset': 12, 'note': 'pointer into the header'},
        'reserved_label': {'packet': HEADER + b'\x41\x30' + name('com'), 'offset': 12, 'note': '0x41 has the reserved 01 prefix'},
        'too_long': {'packet': bytes(long_), 'offset': starts[3], 'note': 'four 63-octet labels via pointers: 257 octets'},
        'truncated': {'packet': HEADER + b'\x0aorder', 'offset': 12, 'note': 'label claims 10 octets, 5 remain'},
    }


def decode_name(msg, offset, max_hops=16, backward_only=True, min_target=12, max_length=255):
    pos, hops, wire_len, labels, nxt = offset, 0, 0, [], None
    trace = [f'start at offset {offset}; max_hops={max_hops}, backward_only={backward_only}, '
             f'min_target={min_target}, max_length={max_length}, packet {len(msg)} octets']
    steps = 0
    while True:
        steps += 1
        if steps > SAFETY_CAP:
            raise NameError_('no bound stopped the decoder: it would loop forever', trace)
        if pos >= len(msg):
            raise NameError_(f'read past the end at offset {pos}', trace)
        b = msg[pos]
        prefix = b >> 6
        if prefix == 0 and b == 0:
            wire_len += 1
            if wire_len > max_length:
                raise NameError_(f'name is {wire_len} octets on the wire, over {max_length}', trace)
            if nxt is None:
                nxt = pos + 1
            trace.append(f'{pos}: root label; name complete, {wire_len} octets; caller continues at {nxt}')
            return {'name': '.'.join(labels) + '.', 'next_offset': nxt, 'hops': hops, 'wire_length': wire_len, 'trace': trace}
        if prefix == 0:
            end = pos + 1 + b
            if end > len(msg):
                raise NameError_(f'label at {pos} claims {b} octets but only {len(msg) - pos - 1} remain', trace)
            wire_len += 1 + b
            if wire_len + 1 > max_length:
                raise NameError_(f'name would be at least {wire_len + 1} octets on the wire, over {max_length}', trace)
            text = msg[pos + 1:end].decode('ascii', 'replace')
            labels.append(text)
            trace.append(f'{pos}: label of {b} octets "{text[:12]}{"..." if len(text) > 12 else ""}"; wire length {wire_len}')
            pos = end
            continue
        if prefix != 3:
            raise NameError_(f'octet 0x{b:02x} at {pos} uses the reserved {prefix:02b} prefix', trace)
        if pos + 1 >= len(msg):
            raise NameError_(f'pointer at {pos} is cut off', trace)
        target = ((b & 0x3f) << 8) | msg[pos + 1]
        hops += 1
        if nxt is None:
            nxt = pos + 2
        trace.append(f'{pos}: pointer {hops} to offset {target}')
        if max_hops and hops > max_hops:
            raise NameError_(f'more than {max_hops} pointers', trace)
        if target >= len(msg):
            raise NameError_(f'pointer at {pos} targets {target}, beyond the {len(msg)}-octet packet', trace)
        if target < min_target:
            raise NameError_(f'pointer at {pos} targets {target}, inside the header', trace)
        if backward_only and target >= pos:
            raise NameError_(f'pointer at {pos} targets {target}, which is not before it', trace)
        pos = target


def run_all(**options):
    out = {}
    for key, f in build_fixtures().items():
        try:
            r = decode_name(f['packet'], f['offset'], **options)
            out[key] = {'ok': True, 'name': r['name'], 'next_offset': r['next_offset'], 'hops': r['hops'], 'wire_length': r['wire_length']}
        except NameError_ as e:
            out[key] = {'ok': False, 'error': e.args[0]}
    return out


def main():
    if '--json' in sys.argv:
        fx = {k: {'hex': v['packet'].hex(), 'offset': v['offset'], 'note': v['note']} for k, v in build_fixtures().items()}
        print(json.dumps({'fixtures': fx, 'strict': run_all(), 'lenient_hops8': run_all(backward_only=False, max_hops=8)}, indent=1))
        return
    for title, opts in (('strict (backward only, 16 hops)', {}), ('lenient (forward allowed, 8 hops)', {'backward_only': False, 'max_hops': 8}),
                        ('no bounds (forward allowed, no hop limit)', {'backward_only': False, 'max_hops': 0})):
        print('==', title)
        for k, v in run_all(**opts).items():
            print(f'  {k:17} ' + (f"{v['name']} next={v['next_offset']} hops={v['hops']} len={v['wire_length']}" if v['ok'] else 'REFUSED: ' + v['error']))


if __name__ == '__main__':
    main()
