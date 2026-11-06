"""Measure how pretty-printing JSON grows with nesting depth, and format fetched JSON only within limits.

Author: Sandeep Belgavi. Companion to "pydantic-ai 2.66.0: Ten Advisories, Most About Work Done Before a Limit"
(aicassindra.com). Standard library only. This is an illustration of limit-before-work, not pydantic-ai code.
"""
import json


def nested(depth, leaves=0):
    return '[' * depth + ','.join(['0'] * leaves) + ']' * depth


def growth(raw):
    obj = json.loads(raw)
    pretty = json.dumps(obj, indent=2)
    return {'raw_bytes': len(raw), 'indented_bytes': len(pretty), 'compact_bytes': len(json.dumps(obj)),
            'growth': round(len(pretty) / len(raw))}


def max_depth(text):
    """Linear scan for bracket depth outside strings."""
    depth = deepest = 0
    in_string = escaped = False
    for ch in text:
        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in '[{':
            depth += 1
            deepest = max(deepest, depth)
        elif ch in ']}':
            depth -= 1
    return deepest


def bounded_pretty(raw: bytes, max_bytes: int = 200_000, max_depth_allowed: int = 64) -> str:
    if len(raw) > max_bytes:
        raise ValueError('response too large')
    text = raw.decode('utf-8', 'replace')
    if max_depth(text) > max_depth_allowed:
        raise ValueError('JSON nested too deeply to format')
    return json.dumps(json.loads(text), indent=2)[:max_bytes]


if __name__ == '__main__':
    for depth, leaves in ((500, 0), (900, 0), (400, 100_000)):
        print(json.dumps({'depth': depth, 'leaves': leaves, **growth(nested(depth, leaves))}))
