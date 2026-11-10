"""Client-side acceptance of an MCP tools/call result that declares an outputSchema.

Author: Sandeep Belgavi. The validator below deliberately supports a small JSON Schema subset and
fails closed on anything else, including any $ref that is not a local #/$defs pointer. In a real
client prefer a maintained JSON Schema 2020-12 validator and keep this policy wrapper around it.
No network access, no MCP server and no model call.
"""
SUPPORTED = {'$schema', '$defs', '$ref', 'type', 'properties', 'required', 'additionalProperties',
             'items', 'enum', 'minimum', 'maximum', 'maxLength', 'description', 'title'}
MAX_DEPTH = 32


class Unsupported(Exception):
    pass


def _type_ok(kind, value):
    return {
        'object': isinstance(value, dict),
        'array': isinstance(value, list),
        'string': isinstance(value, str),
        'integer': isinstance(value, int) and not isinstance(value, bool),
        'number': isinstance(value, (int, float)) and not isinstance(value, bool),
        'boolean': isinstance(value, bool),
        'null': value is None,
    }.get(kind)


def _resolve(ref, root):
    if not ref.startswith('#/$defs/'):
        raise Unsupported(f'non-local $ref {ref!r} is not dereferenced')
    name = ref[len('#/$defs/'):]
    if name not in root.get('$defs', {}):
        raise Unsupported(f'unresolved $ref {ref!r}')
    return root['$defs'][name]


def validate(schema, value, root=None, path='$', depth=0):
    """Return a list of error strings. Raise Unsupported for schemas outside the subset."""
    root = schema if root is None else root
    if depth > MAX_DEPTH:
        raise Unsupported('schema nesting exceeds the depth limit')
    if not isinstance(schema, dict):
        raise Unsupported('schema must be an object')
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise Unsupported('unsupported keywords: ' + ', '.join(sorted(unknown)))
    if '$ref' in schema:
        return validate(_resolve(schema['$ref'], root), value, root, path, depth + 1)
    errors = []
    kind = schema.get('type')
    if kind is not None:
        ok = _type_ok(kind, value)
        if ok is None:
            raise Unsupported(f'unknown type {kind!r}')
        if not ok:
            return [f'{path}: expected {kind}']
    if 'enum' in schema and value not in schema['enum']:
        errors.append(f'{path}: {value!r} not in enum')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if 'minimum' in schema and value < schema['minimum']:
            errors.append(f'{path}: below minimum')
        if 'maximum' in schema and value > schema['maximum']:
            errors.append(f'{path}: above maximum')
    if isinstance(value, str) and 'maxLength' in schema and len(value) > schema['maxLength']:
        errors.append(f'{path}: longer than maxLength')
    if isinstance(value, dict):
        props = schema.get('properties', {})
        for name in schema.get('required', []):
            if name not in value:
                errors.append(f'{path}.{name}: required')
        for name, item in value.items():
            if name in props:
                errors += validate(props[name], item, root, f'{path}.{name}', depth + 1)
            elif schema.get('additionalProperties') is False:
                errors.append(f'{path}.{name}: not allowed')
    if isinstance(value, list) and 'items' in schema:
        for i, item in enumerate(value):
            errors += validate(schema['items'], item, root, f'{path}[{i}]', depth + 1)
    return errors


def accept(tool, result):
    """Decide what the client may hand to the model or to code. Returns (status, detail)."""
    if result.get('isError') is True:
        return 'tool_error', result.get('content', [])
    schema = tool.get('outputSchema')
    if schema is None:
        return 'unstructured', result.get('content', [])
    if 'structuredContent' not in result:
        return 'protocol_violation', 'outputSchema declared but structuredContent missing'
    try:
        errors = validate(schema, result['structuredContent'])
    except Unsupported as exc:
        return 'schema_unsupported', str(exc)
    if errors:
        return 'invalid_structured_content', errors
    return 'accepted', result['structuredContent']


ORDER_STATUS_TOOL = {
    'name': 'get_order_status',
    'inputSchema': {'type': 'object', 'properties': {'order_id': {'type': 'string'}}, 'required': ['order_id']},
    'outputSchema': {
        'type': 'object',
        'properties': {
            'order_id': {'type': 'string'},
            'status': {'enum': ['packed', 'shipped', 'delivered', 'returned']},
            'refund_eligible': {'type': 'boolean'},
            'items': {'type': 'array', 'items': {'$ref': '#/$defs/line'}},
        },
        'required': ['order_id', 'status', 'refund_eligible'],
        'additionalProperties': False,
        '$defs': {'line': {'type': 'object', 'properties': {'isbn': {'type': 'string'}, 'qty': {'type': 'integer', 'minimum': 1}},
                           'required': ['isbn', 'qty']}},
    },
}
