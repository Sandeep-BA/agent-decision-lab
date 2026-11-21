# Bounded decoding of compressed DNS names

**Author: Sandeep Belgavi**

A runnable companion to *Decode DNS Names Without Following Compression Pointers Forever* (aicassindra.com). Decodes names from eight synthetic packets under example.com with checks from RFC 1035 section 4.1.4 and RFC 9267: bounds, reserved 01/10 label prefixes, pointers into the header, backward-only pointers, a pointer-hop limit and the 255-octet name limit. It returns the next wire offset, which is two octets after the first pointer.

## Prerequisites

- Python 3.11 or newer (run here with CPython 3.13.5 on Windows). Standard library only.
- `.env.example` documents that nothing secret is read from the environment.

## Sample input

`build_fixtures()`; `python dns_names.py --json` prints the packets as hex for the companion lab.

## Commands

From this directory:

```
python dns_names.py
python -m unittest -v
```

## Expected output

`valid`: help.books.example.com., next offset 42, 1 pointer, 24 octets. Strict mode refuses the self-loop, two-pointer loop and forward pointer as "not before it", the header pointer, the 0x41 octet, a 257-octet name and a truncated label. With forward pointers allowed and 8 hops the loops stop at "more than 8 pointers"; with no bounds they would loop forever. 6 tests pass.

## Limitations

Name decoding only; no resource-record parsing, EDNS or DNSSEC. Not a resolver.

Views are my own and do not represent any employer, past or present.
