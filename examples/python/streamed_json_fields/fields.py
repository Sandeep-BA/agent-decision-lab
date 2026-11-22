# Author: Sandeep Belgavi. Track which top-level fields of a streamed JSON object are complete.
# Synthetic chunks for a help-desk proposal at the fictional Belgavi's Book Store; no model calls.
"""Run: python fields.py"""
import json

WS = ' \t\r\n'
BACKSLASH = chr(92)


def complete_fields(buf):
    """Return {key: value} for top-level fields whose value is certainly finished.

    A string is finished at its closing quote, an object or array at its matching bracket,
    and a number or literal only once a delimiter follows it, because "12" may become "125".
    """
    out, n = {}, len(buf)

    def skip(j):
        while j < n and buf[j] in WS:
            j += 1
        return j

    def end_of_string(j):  # j at the opening quote; index after the closing quote, or None
        j += 1
        while j < n:
            if buf[j] == BACKSLASH:
                j += 2
                continue
            if buf[j] == '"':
                return j + 1
            j += 1
        return None

    def end_of_value(j):
        if j >= n:
            return None
        if buf[j] == '"':
            return end_of_string(j)
        if buf[j] in '{[':
            depth, k = 0, j
            while k < n:
                if buf[k] == '"':
                    k = end_of_string(k)
                    if k is None:
                        return None
                    continue
                if buf[k] in '{[':
                    depth += 1
                elif buf[k] in '}]':
                    depth -= 1
                    if depth == 0:
                        return k + 1
                k += 1
            return None
        k = j
        while k < n and buf[k] not in ',}' + WS:
            k += 1
        return k if k < n else None  # no delimiter yet: the number or literal may still grow

    i = skip(0)
    if i >= n or buf[i] != '{':
        return out
    i += 1
    while True:
        i = skip(i)
        if i >= n or buf[i] != '"':
            return out
        kend = end_of_string(i)
        if kend is None:
            return out
        key = json.loads(buf[i:kend])
        i = skip(kend)
        if i >= n or buf[i] != ':':
            return out
        vstart = skip(i + 1)
        vend = end_of_value(vstart)
        if vend is None:
            return out
        out[key] = json.loads(buf[vstart:vend])
        i = skip(vend)
        if i < n and buf[i] == ',':
            i += 1
        else:
            return out


def naive_repair(buf):
    """A 'close what is open and parse' preview. Its values may still change."""
    stack, in_str, esc = [], False, False
    for c in buf:
        if in_str:
            if esc:
                esc = False
            elif c == BACKSLASH:
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c in '{[':
            stack.append('}' if c == '{' else ']')
        elif c in '}]':
            stack.pop()
    s = buf + ('"' if in_str else '')
    s = s.rstrip().rstrip(',')
    try:
        return json.loads(s + ''.join(reversed(stack)))
    except json.JSONDecodeError:
        return None


CHUNKS = ['{"case_id": "CASE-4201", "action": "ref', 'und", "amount": 12',
          '5, "items": [{"sku": "BK-7"', '}], "note": "Damaged cov', 'er"}']


def run(chunks=CHUNKS):
    buf, steps = '', []
    for c in chunks:
        buf += c
        steps.append({'received': len(buf), 'complete': complete_fields(buf), 'naive': naive_repair(buf)})
    return steps


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
