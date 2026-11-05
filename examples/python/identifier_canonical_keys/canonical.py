"""Canonical keys for user-chosen identifiers: one key for uniqueness, one for look-alike review.

Author: Sandeep Belgavi.

username_key() follows the order of the PRECIS UsernameCaseMapped profile (RFC 8265 section 3.3):
width mapping, case mapping, NFC, then a simplified check that rejects characters the profile would
disallow. It is an illustration of the order and the failure modes, not a complete PRECIS
implementation: it does not implement the full IdentifierClass derivation or the Bidi Rule.

skeleton() follows UTS #39 section 4: NFD, map every character through confusables.txt, NFD again.
Two identifiers with the same skeleton look alike; that is a review signal, not a uniqueness key.
"""
from __future__ import annotations

import pathlib
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent


class Rejected(ValueError):
    """The identifier contains a character this policy refuses to store."""


def _width_map(text: str) -> str:
    out = []
    for ch in text:
        decomposition = unicodedata.decomposition(ch)
        if decomposition.startswith(('<wide>', '<narrow>')):
            out.append(chr(int(decomposition.split()[1], 16)))
        else:
            out.append(ch)
    return ''.join(out)


def _check(text: str) -> None:
    if not text:
        raise Rejected('empty identifier')
    for ch in text:
        category = unicodedata.category(ch)
        if category in ('Cc', 'Cf', 'Co', 'Cn', 'Zs', 'Zl', 'Zp'):
            raise Rejected('U+%04X %s is not allowed (%s)' % (ord(ch), unicodedata.name(ch, '?'), category))
        if category.startswith('M') and text.index(ch) == 0:
            raise Rejected('identifier starts with a combining mark')


def username_key(raw: str) -> str:
    """The value to put under a UNIQUE index. Store the user's original spelling separately for display."""
    text = _width_map(raw)
    text = text.lower()            # RFC 8265 uses toLowerCase(), not case folding: 'ß' stays 'ß'
    text = unicodedata.normalize('NFC', text)
    _check(text)
    return text


def load_confusables(path: pathlib.Path | None = None) -> dict[str, str]:
    table = {}
    for line in (path or HERE / 'confusables_subset.txt').read_text(encoding='utf-8').splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        source, target, _kind = (field.strip() for field in line.split(';'))
        table[chr(int(source, 16))] = ''.join(chr(int(cp, 16)) for cp in target.split())
    return table


def skeleton(text: str, table: dict[str, str]) -> str:
    """UTS #39 skeleton(X): NFD, replace each character by its confusables prototype, NFD."""
    decomposed = unicodedata.normalize('NFD', text)
    return unicodedata.normalize('NFD', ''.join(table.get(ch, ch) for ch in decomposed))


def naive_keys(raw: str) -> dict[str, str]:
    """What three common shortcuts would store, for comparison."""
    return {'as_typed': raw, 'lower': raw.lower(), 'casefold_nfkc': unicodedata.normalize('NFKC', raw.casefold())}
