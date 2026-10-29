"""Assemble streamed tool-call arguments from Claude, OpenAI Responses and Gemini Interactions event shapes.

Author: Sandeep Belgavi. Companion to "Assembling Streamed Tool-Call Arguments Across Providers" (aicassindra.com).
The streams below are synthetic recordings shaped like each provider's documented events; nothing calls an API.
"""
import json


class ToolCallAccumulator:
    def __init__(self):
        self.calls = {}

    def start(self, key, call_id, name, initial=''):
        self.calls[key] = {'id': call_id, 'name': name, 'buf': initial, 'done': False}

    def fragment(self, key, text):
        call = self.calls.get(key)
        if call is None or call['done']:
            raise ValueError('fragment for unknown or finished call %r' % (key,))
        call['buf'] += text

    def finish(self, key, final_arguments=None):
        call = self.calls[key]
        call['done'] = True
        if final_arguments is not None and final_arguments != call['buf']:
            call['mismatch'] = True
            call['buf'] = final_arguments
        try:
            return call, json.loads(call['buf'] or '{}')
        except json.JSONDecodeError:
            return call, None


def feed_claude(events, acc):
    finished = []
    for e in events:
        t = e['type']
        if t == 'content_block_start' and e['content_block']['type'] == 'tool_use':
            acc.start(e['index'], e['content_block']['id'], e['content_block']['name'])
        elif t == 'content_block_delta' and e['delta']['type'] == 'input_json_delta':
            acc.fragment(e['index'], e['delta']['partial_json'])
        elif t == 'content_block_stop' and e['index'] in acc.calls:
            finished.append(acc.finish(e['index']))
    return finished


def feed_openai(events, acc):
    finished = []
    for e in events:
        t = e['type']
        if t == 'response.output_item.added' and e['item']['type'] == 'function_call':
            acc.start(e['output_index'], e['item']['call_id'], e['item']['name'], e['item'].get('arguments', ''))
        elif t == 'response.function_call_arguments.delta':
            acc.fragment(e['output_index'], e['delta'])
        elif t == 'response.function_call_arguments.done':
            finished.append(acc.finish(e['output_index'], e.get('arguments')))
    return finished


def feed_gemini(events, acc):
    finished = []
    for e in events:
        t = e['event_type']
        if t == 'step.start' and e['step']['type'] == 'function_call':
            args = e['step'].get('arguments') or ''
            acc.start(e['index'], e['step']['id'], e['step']['name'], json.dumps(args) if isinstance(args, dict) else args)
        elif t == 'step.delta' and e['delta']['type'] == 'arguments' and e['index'] in acc.calls:
            acc.fragment(e['index'], e['delta']['partial_arguments'])
        elif t == 'interaction.completed':
            finished.extend(acc.finish(k) for k in sorted(acc.calls) if not acc.calls[k]['done'])
    return finished


REFUND_SCHEMA = {'required': ('order_id', 'amount', 'note'), 'max_amount': {'BK-58213': 1173.0}}


def gate(call, parsed, schema=REFUND_SCHEMA):
    """Decide whether a finished call may execute. Returns ('execute', args) or ('error', tool_result)."""
    if parsed is None:
        return 'error', {'tool_use_id': call['id'], 'is_error': True,
                         'content': json.dumps({'INVALID_JSON': call['buf']})}
    missing = [k for k in schema['required'] if k not in parsed]
    if missing:
        return 'error', {'tool_use_id': call['id'], 'is_error': True, 'content': 'missing arguments: ' + ', '.join(missing)}
    limit = schema['max_amount'].get(parsed['order_id'])
    if limit is None or not 0 < parsed['amount'] <= limit:
        return 'error', {'tool_use_id': call['id'], 'is_error': True, 'content': 'amount outside the order total'}
    return 'execute', parsed


def split_everywhere(text, step=1):
    """All fragmentations of text into two pieces, plus single-character fragments."""
    for i in range(1, len(text), step):
        yield [text[:i], text[i:]]
    yield list(text)


ARGS_A = {'order_id': 'BK-58213', 'amount': 349.0, 'note': 'Refund for the damaged copy of Kindred — “spine split”, per Tanishka.'}
ARGS_B = {'order_id': 'BK-58213', 'amount': 25.0, 'note': 'Shipping refund.'}


def claude_stream(pieces_a, pieces_b, truncate=False):
    ev = [{'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}},
          {'type': 'content_block_stop', 'index': 0},
          {'type': 'content_block_start', 'index': 1, 'content_block': {'type': 'tool_use', 'id': 'toolu_A', 'name': 'issue_refund', 'input': {}}},
          {'type': 'content_block_start', 'index': 2, 'content_block': {'type': 'tool_use', 'id': 'toolu_B', 'name': 'issue_refund', 'input': {}}}]
    # interleave the two calls' fragments to exercise keying by index
    for i in range(max(len(pieces_a), len(pieces_b))):
        if i < len(pieces_a):
            ev.append({'type': 'content_block_delta', 'index': 1, 'delta': {'type': 'input_json_delta', 'partial_json': pieces_a[i]}})
        if i < len(pieces_b):
            ev.append({'type': 'content_block_delta', 'index': 2, 'delta': {'type': 'input_json_delta', 'partial_json': pieces_b[i]}})
    ev += [{'type': 'content_block_stop', 'index': 1}, {'type': 'content_block_stop', 'index': 2}]
    return ev


def openai_stream(pieces, full):
    ev = [{'type': 'response.output_item.added', 'output_index': 0, 'item': {'type': 'function_call', 'id': 'fc_1', 'call_id': 'call_1', 'name': 'issue_refund', 'arguments': ''}}]
    ev += [{'type': 'response.function_call_arguments.delta', 'output_index': 0, 'item_id': 'fc_1', 'delta': p} for p in pieces]
    ev.append({'type': 'response.function_call_arguments.done', 'output_index': 0, 'item_id': 'fc_1', 'arguments': full})
    return ev


def gemini_stream(pieces):
    ev = [{'event_type': 'step.start', 'index': 0, 'step': {'type': 'function_call', 'id': 'fn_1', 'name': 'issue_refund', 'arguments': ''}}]
    ev += [{'event_type': 'step.delta', 'index': 0, 'delta': {'type': 'arguments', 'partial_arguments': p}} for p in pieces]
    ev.append({'event_type': 'interaction.completed'})
    return ev


def main():
    a, b = json.dumps(ARGS_A), json.dumps(ARGS_B)
    rows = []
    acc = ToolCallAccumulator()
    for call, parsed in feed_claude(claude_stream([a[:17], a[17:40], a[40:]], [b[:5], b[5:]]), acc):
        rows.append(('claude', call['id'], gate(call, parsed)[0]))
    acc = ToolCallAccumulator()
    for call, parsed in feed_openai(openai_stream([a[:9], a[9:]], a), acc):
        rows.append(('openai', call['id'], gate(call, parsed)[0]))
    acc = ToolCallAccumulator()
    for call, parsed in feed_gemini(gemini_stream([a[:30], a[30:]]), acc):
        rows.append(('gemini', call['id'], gate(call, parsed)[0]))
    truncated = a[:a.index('"note"') - 2]          # stream ended (max_tokens) after the amount
    acc = ToolCallAccumulator()
    for call, parsed in feed_claude(claude_stream([truncated], [b]), acc):
        rows.append(('claude truncated', call['id'], gate(call, parsed)[0]))
    for r in rows:
        print('%-18s %-8s %s' % r)


if __name__ == '__main__':
    main()
