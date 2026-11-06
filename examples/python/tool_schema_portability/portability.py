"""Check one tool JSON Schema against documented subsets for OpenAI strict mode, Claude strict tool use and the
google-genai SDK's JSON Schema to Schema conversion.

Author: Sandeep Belgavi. Companion to "One Tool Schema, Four Consumers" (aicassindra.com). Standard library only.
The subsets encode documentation read on 2026-11-06; they are not the providers' grammars. Re-read the docs
before trusting a result, and send one real request per provider before production.
"""
import json
import sys

UNSUPPORTED = {
    'openai_strict': {'allOf', 'not', 'if', 'then', 'else', 'dependentRequired', 'dependentSchemas'},
    'claude_strict': {'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf', 'minLength', 'maxLength'},
    'gemini_sdk_schema': {'const', 'multipleOf', 'exclusiveMinimum', 'exclusiveMaximum'},
}
DESCRIPTION_HINTS = ('minimum', 'maximum', 'multipleOf', 'minLength', 'maxLength', 'exclusiveMaximum', 'exclusiveMinimum')


def walk(node, path='$'):
    if isinstance(node, dict):
        yield path, node
        for key, child in node.items():
            if key in ('properties', '$defs'):
                for name, sub in child.items():
                    yield from walk(sub, f'{path}.{key}.{name}')
            elif isinstance(child, (dict, list)):
                yield from walk(child, f'{path}.{key}')
    elif isinstance(node, list):
        for i, child in enumerate(node):
            yield from walk(child, f'{path}[{i}]')


def problems(schema, target):
    found = []
    for path, node in walk(schema):
        for key in sorted(UNSUPPORTED[target] & set(node)):
            found.append(f'{path}: {key}')
        if node.get('type') == 'object' and 'properties' in node:
            if node.get('additionalProperties') is not False and target != 'gemini_sdk_schema':
                found.append(f'{path}: additionalProperties must be false')
            if target == 'openai_strict' and set(node['properties']) - set(node.get('required', [])):
                missing = sorted(set(node['properties']) - set(node.get('required', [])))
                found.append(f'{path}: every property must be required (missing {", ".join(missing)})')
    return found


def portable_core(schema, target):
    """Drop keywords the target refuses and move numeric and length limits into the description as text."""
    if isinstance(schema, list):
        return [portable_core(x, target) for x in schema]
    if not isinstance(schema, dict):
        return schema
    out, hints = {}, []
    for key, value in schema.items():
        if key in UNSUPPORTED[target]:
            if key in DESCRIPTION_HINTS:
                hints.append(f'{key} {value}')
            continue
        if key in ('properties', '$defs'):
            out[key] = {k: portable_core(v, target) for k, v in value.items()}
        else:
            out[key] = portable_core(value, target)
    if hints:
        out['description'] = (out.get('description', '') + ' (' + ', '.join(hints) + ')').strip()
    if target == 'openai_strict' and out.get('type') == 'object' and 'properties' in out:
        for name in sorted(set(out['properties']) - set(out.get('required', []))):
            prop = out['properties'][name]
            if 'anyOf' not in prop:
                out['properties'][name] = {'anyOf': [prop, {'type': 'null'}]}
        out['required'] = list(out['properties'])
    return out


if __name__ == '__main__':
    schema = json.load(open(sys.argv[1], encoding='utf-8'))
    for target in UNSUPPORTED:
        print(target, json.dumps(problems(schema, target)))
    print('claude core', json.dumps(portable_core(schema, 'claude_strict')['properties']['amount']))
