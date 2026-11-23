"""Build-time assignability check for workflow edges. Author: Sandeep Belgavi.

An original Python model of the rules ADK Java 1.15.0 documents in
com.google.adk.workflow.SchemaFit (read at tag v1.15.0): an edge is accepted
when the source node's output schema fits the target node's input schema by
types, enums, keys and nullability. Formats, patterns and numeric bounds are
ignored at build time. This model covers type, enum, nullable, items,
properties and required; it does not model anyOf unions or the reading of
untyped enum strings as numbers, which ADK also handles. It is not ADK code.

Schemas are plain dicts: {"type": "object", "properties": {...},
"required": [...], "nullable": true, "enum": [...], "items": {...}}.
"""
from __future__ import annotations

import json


def _accepts_null(s: dict) -> bool:
    return bool(s.get('nullable')) or s.get('type') == 'null' or ('type' not in s and 'enum' not in s)


def _declares_keys(s: dict) -> bool:
    return 'properties' in s or 'required' in s


def fits(source: dict, target: dict, closed: bool = False, path: str = '$') -> tuple[bool, str]:
    """Return (fits, reason). closed: objects in target that list properties take no other key."""
    if source == target:
        return True, 'identical'
    stype = source.get('type')
    if source.get('nullable') or stype == 'null':
        if not _accepts_null(target):
            return False, f'{path}: source may be null, target does not accept null'
        if stype == 'null':
            return True, 'null into nullable'
        return fits({k: v for k, v in source.items() if k != 'nullable'}, target, closed, path)
    if stype is None and 'enum' in source:
        return fits(dict(source, type='string'), target, closed, path)
    if stype is None:
        return True, f'{path}: untyped source fits anything that is not null-only'
    if 'enum' in target and not ('enum' in source and set(source['enum']) <= set(target['enum'])):
        extra = sorted(set(source.get('enum', ['<any string>'])) - set(target['enum']))
        return False, f'{path}: source can produce {extra} outside target enum'
    ttype = target.get('type')
    if ttype is not None and ttype != stype and not (stype == 'integer' and ttype == 'number'):
        return False, f'{path}: {stype} does not fit {ttype}'
    if stype == 'array':
        if 'items' not in target or 'items' not in source:
            return True, 'array without item schema on one side'
        return fits(source['items'], target['items'], closed, path + '[]')
    if stype == 'object':
        return _object_fits(source, target, closed, path)
    return True, 'types fit'


def _object_fits(source: dict, target: dict, closed: bool, path: str) -> tuple[bool, str]:
    if not _declares_keys(source):
        return True, f'{path}: source object declares no keys (a map); the build cannot know its keys'
    given, wanted = source.get('properties', {}), target.get('properties', {})
    required, target_required = set(source.get('required', [])), set(target.get('required', []))
    missing = sorted(target_required - required)
    if missing:
        return False, f'{path}: target requires {missing}, source does not guarantee them'
    undeclared = sorted(k for k in target_required if k in wanted and k not in given)
    if undeclared:
        return False, f'{path}: target declares and requires {undeclared}, source does not declare them'
    closed_target = closed and 'properties' in target
    if closed_target and not required <= set(wanted):
        return False, f'{path}: closed target takes no key {sorted(required - set(wanted))}'
    for key, sub in given.items():
        if key in wanted:
            ok, why = fits(sub, wanted[key], closed, f'{path}.{key}')
            if not ok:
                return False, why
        elif closed_target:
            return False, f'{path}: closed target takes no key {key!r}'
    return True, 'object keys fit'


S = lambda t, **kw: dict(type=t, **kw)
REFUND_OUT = S('object', properties={'case_id': S('string'), 'amount': S('integer'), 'reason': S('string', enum=['damaged', 'late'])},
               required=['case_id', 'amount', 'reason'])
CASES = [
    ('integer into number', S('integer'), S('number'), False),
    ('number into integer', S('number'), S('integer'), False),
    ('enum subset', S('string', enum=['damaged', 'late']), S('string', enum=['damaged', 'late', 'wrong_item']), False),
    ('enum superset', S('string', enum=['damaged', 'late', 'other']), S('string', enum=['damaged', 'late']), False),
    ('nullable into non-null', S('string', nullable=True), S('string'), False),
    ('refund into wider open object', REFUND_OUT, S('object', properties={'case_id': S('string'), 'amount': S('number')}, required=['case_id']), False),
    ('refund into closed inferred record', REFUND_OUT, S('object', properties={'case_id': S('string'), 'amount': S('number')}, required=['case_id']), True),
    ('missing required key', S('object', properties={'case_id': S('string')}, required=['case_id']), S('object', properties={'case_id': S('string'), 'amount': S('number')}, required=['case_id', 'amount']), False),
    ('map output into record input', S('object'), S('object', properties={'case_id': S('string')}, required=['case_id']), True),
    ('bounds ignored at build time', S('integer'), S('integer', minimum=1, maximum=500), False),
]


def run() -> list[dict]:
    return [{'edge': name, 'closed': closed, 'fits': fits(src, dst, closed)[0], 'reason': fits(src, dst, closed)[1]}
            for name, src, dst, closed in CASES]


if __name__ == '__main__':
    for row in run():
        print(json.dumps(row))
