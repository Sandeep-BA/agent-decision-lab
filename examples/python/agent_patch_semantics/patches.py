"""Partial updates from an agent: RFC 7396 merge patch versus RFC 6902 JSON Patch compiled from typed intent.

Author: Sandeep Belgavi. Original example for the aicassindra.com article "Partial Updates From Agents:
Merge Patch Nulls, JSON Patch Tests and Field Masks". Standard library only; no model or server is called.
Run: python patches.py fixtures/tanishka.json
"""
import copy
import json
import sys


def merge_patch(target, patch):
    """RFC 7396 section 2, implemented from the pseudocode."""
    if not isinstance(patch, dict):
        return copy.deepcopy(patch)
    result = copy.deepcopy(target) if isinstance(target, dict) else {}
    for name, value in patch.items():
        if value is None:
            result.pop(name, None)
        else:
            result[name] = merge_patch(result.get(name), value)
    return result


class PatchConflict(Exception):
    """A test operation failed; RFC 6902 says the whole document is not applied."""


def _resolve(doc, path):
    """Return (parent, last token) for an RFC 6901 pointer. Supports object members and array indices."""
    if not path.startswith('/'):
        raise ValueError('JSON Pointer must start with /: ' + path)
    tokens = [t.replace('~1', '/').replace('~0', '~') for t in path[1:].split('/')]
    parent = doc
    for t in tokens[:-1]:
        parent = parent[int(t)] if isinstance(parent, list) else parent[t]
    return parent, tokens[-1]


def apply_json_patch(doc, ops):
    """Apply add, remove, replace and test atomically: on any failure the original is returned unchanged."""
    work = copy.deepcopy(doc)
    for op in ops:
        parent, key = _resolve(work, op['path'])
        kind = op['op']
        if kind == 'test':
            current = parent[int(key)] if isinstance(parent, list) else parent.get(key, _MISSING)
            if current != op['value']:
                raise PatchConflict('test failed at %s: expected %r, found %r' % (op['path'], op['value'], current))
        elif kind == 'add':
            if isinstance(parent, list):
                parent.insert(len(parent) if key == '-' else int(key), copy.deepcopy(op['value']))
            else:
                parent[key] = copy.deepcopy(op['value'])
        elif kind == 'remove':
            if isinstance(parent, list):
                del parent[int(key)]
            else:
                del parent[key]
        elif kind == 'replace':
            if isinstance(parent, list):
                parent[int(key)] = copy.deepcopy(op['value'])
            else:
                if key not in parent:
                    raise PatchConflict('replace target missing: ' + op['path'])
                parent[key] = copy.deepcopy(op['value'])
        else:
            raise ValueError('unsupported op: ' + kind)
    return work


_MISSING = object()
ALLOWED = {"/phone", "/addresses", "/marketing_opt_in"}


def compile_ops(intent, read_copy):
    """Same function as in the article: typed intent from the model becomes JSON Patch operations."""
    ops = []
    for action, field, value in intent:
        path = "/" + field
        if path not in ALLOWED:
            raise ValueError("field not editable by this tool: " + field)
        if action == "append":
            ops.append({"op": "add", "path": path + "/-", "value": value})
        elif action == "set":
            if field in read_copy:
                ops.append({"op": "test", "path": path, "value": read_copy[field]})
            ops.append({"op": "add", "path": path, "value": value})
        elif action == "remove":
            ops.append({"op": "test", "path": path, "value": read_copy[field]})
            ops.append({"op": "remove", "path": path})
        else:
            raise ValueError("unknown action: " + action)
    return ops


def run(fixture):
    record = fixture['record']
    stored = merge_patch(record, fixture['website_change'])           # the concurrent website edit
    merged = merge_patch(stored, fixture['model_merge_patch'])        # what the free-form tool sent
    ops = compile_ops([tuple(i) for i in fixture['intent']], record)  # the typed tool, from the agent's read
    typed = apply_json_patch(stored, ops)
    consent_ops = compile_ops([('set', 'marketing_opt_in', False)], record)
    try:
        apply_json_patch(stored, consent_ops)
        consent = 'applied'
    except PatchConflict as e:
        consent = 'conflict: ' + str(e)
    return {
        'merge_patch': {'addresses': len(merged.get('addresses', [])), 'phone': merged.get('phone', 'deleted'),
                        'marketing_opt_in': merged.get('marketing_opt_in')},
        'typed_json_patch': {'ops': ops, 'addresses': len(typed['addresses']), 'phone': typed['phone'],
                             'marketing_opt_in': typed['marketing_opt_in']},
        'stale_consent_change': consent,
    }


if __name__ == '__main__':
    with open(sys.argv[1] if len(sys.argv) > 1 else 'fixtures/tanishka.json', encoding='utf-8') as f:
        print(json.dumps(run(json.load(f)), indent=2))
