"""Normalise stop reasons from three response shapes and refuse to parse incomplete output.
Author: Sandeep Belgavi. Standard library only; the fixtures are hand-written response bodies,
not recorded provider calls.
"""
import json

COMPLETE, TRUNCATED, TOOL, BLOCKED, PAUSED, UNKNOWN = 'complete', 'truncated', 'tool', 'blocked', 'paused', 'unknown'

OPENAI_CHAT = {'stop': COMPLETE, 'length': TRUNCATED, 'tool_calls': TOOL, 'function_call': TOOL, 'content_filter': BLOCKED}
OPENAI_RESPONSES_INCOMPLETE = {'max_output_tokens': TRUNCATED, 'content_filter': BLOCKED}
ANTHROPIC = {'end_turn': COMPLETE, 'stop_sequence': COMPLETE, 'max_tokens': TRUNCATED,
             'model_context_window_exceeded': TRUNCATED, 'tool_use': TOOL, 'pause_turn': PAUSED, 'refusal': BLOCKED}
GEMINI = {'STOP': COMPLETE, 'MAX_TOKENS': TRUNCATED, 'SAFETY': BLOCKED, 'RECITATION': BLOCKED,
          'BLOCKLIST': BLOCKED, 'PROHIBITED_CONTENT': BLOCKED, 'SPII': BLOCKED}


def classify(api: str, body: dict) -> tuple[str, str, str]:
    """Return (category, raw_reason, text). Unknown reasons are never treated as complete."""
    if api == 'openai-chat':
        choice = body['choices'][0]
        raw = choice.get('finish_reason')
        return OPENAI_CHAT.get(raw, UNKNOWN), str(raw), choice['message'].get('content') or ''
    if api == 'openai-responses':
        text = ''.join(c.get('text', '') for o in body.get('output', []) if o.get('type') == 'message' for c in o.get('content', []))
        if body.get('status') == 'completed':
            return COMPLETE, 'completed', text
        reason = (body.get('incomplete_details') or {}).get('reason')
        return OPENAI_RESPONSES_INCOMPLETE.get(reason, UNKNOWN), f"{body.get('status')}:{reason}", text
    if api == 'anthropic':
        raw = body.get('stop_reason')
        text = ''.join(b.get('text', '') for b in body.get('content', []) if b.get('type') == 'text')
        return ANTHROPIC.get(raw, UNKNOWN), str(raw), text
    if api == 'gemini':
        cand = body['candidates'][0]
        raw = cand.get('finishReason')
        text = ''.join(p.get('text', '') for p in cand.get('content', {}).get('parts', []))
        return GEMINI.get(raw, UNKNOWN), str(raw), text
    raise ValueError(api)


def accept_json(api: str, body: dict, required: tuple = ()) -> dict:
    """Parse structured output only when generation finished; then check required keys."""
    category, raw, text = classify(api, body)
    if category != COMPLETE:
        return {'ok': False, 'action': {TRUNCATED: 'retry with a larger output budget or a smaller task',
                                        TOOL: 'run the tool and continue', BLOCKED: 'do not retry blindly; route for review',
                                        PAUSED: 'send the turn back to continue', UNKNOWN: 'treat as failure and log the raw reason'}[category],
                'category': category, 'raw': raw}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {'ok': False, 'action': 'complete but invalid JSON: re-ask or use structured outputs', 'category': 'invalid', 'raw': str(exc)}
    missing = [k for k in required if k not in data]
    if missing:
        return {'ok': False, 'action': f'missing keys {missing}', 'category': 'invalid', 'raw': raw}
    return {'ok': True, 'data': data, 'category': COMPLETE, 'raw': raw}


def naive_repair(text: str) -> dict:
    """What NOT to do: cut back to the last complete string item and close the brackets."""
    cut = text[:text.rfind('",') + 1]
    return json.loads(cut + ']}')


TRUNCATED_TEXT = '{"overdue": ["CASE-4101", "CASE-4102", "CASE-41'
FULL_TEXT = '{"overdue": ["CASE-4101", "CASE-4102", "CASE-4103", "CASE-4104", "CASE-4105"]}'

FIXTURES = {
    'openai-chat': {'choices': [{'finish_reason': 'length', 'message': {'content': TRUNCATED_TEXT}}]},
    'openai-responses': {'status': 'incomplete', 'incomplete_details': {'reason': 'max_output_tokens'},
                         'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': TRUNCATED_TEXT}]}]},
    'anthropic': {'stop_reason': 'max_tokens', 'content': [{'type': 'text', 'text': TRUNCATED_TEXT}]},
    'gemini': {'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': [{'text': TRUNCATED_TEXT}]}}]},
}

if __name__ == '__main__':
    for api, body in FIXTURES.items():
        print(api, accept_json(api, body, ('overdue',)))
    print('naive repair keeps', len(naive_repair(TRUNCATED_TEXT)['overdue']), 'of', len(json.loads(FULL_TEXT)['overdue']), 'cases')
