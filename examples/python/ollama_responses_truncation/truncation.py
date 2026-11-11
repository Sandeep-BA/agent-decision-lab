"""Context-overflow handling for an OpenAI-compatible Responses endpoint such as Ollama's.
Author: Sandeep Belgavi.

Offline part (always tested): build requests with an explicit truncation choice, recognise a
context-overflow error with anchored patterns, and check a recorded local run.
Live part (opt-in): `python truncation.py --live` sends one oversized synthetic request per
mode to OLLAMA_URL (default http://127.0.0.1:11434) with OLLAMA_MODEL. It is never run by the tests.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

# Anchored like Ollama's own compaction check, so a user message that merely CONTAINS this text
# does not look like an overflow.
LOCAL_OVERFLOW = re.compile(r'^request \((\d+) tokens\) exceeds the available context size \((\d+) tokens\), try increasing it$')
HOSTED_OVERFLOW = re.compile(r'^The prompt is too long: (\d+), model maximum context length: (\d+)(?: \(ref: [^()]+\))?$')


def request_body(model, text, truncation='disabled', max_output_tokens=64):
    """Always send truncation explicitly; omitting it means 'disabled' in the Responses API and,
    from Ollama 0.40.16, in Ollama too. Older Ollama versions ignored the field."""
    if truncation not in ('disabled', 'auto'):
        raise ValueError(f'unknown truncation strategy: {truncation!r}')
    return {'model': model, 'input': text, 'truncation': truncation, 'max_output_tokens': max_output_tokens}


def overflow(status, body):
    """Return (requested_tokens, context_tokens) for a context-overflow error, else None."""
    if status not in (400, 413):
        return None
    err = (body or {}).get('error') or {}
    if isinstance(err, str):
        msg, code = err, None
    else:
        msg, code = err.get('message') or '', err.get('code')
    for pattern in (LOCAL_OVERFLOW, HOSTED_OVERFLOW):
        m = pattern.match(msg)
        if m:
            return int(m.group(1)), int(m.group(2))
    if code == 'context_length_exceeded':
        return (-1, -1)
    return None


def kept_fraction(usage_input_tokens, requested_tokens):
    """With truncation=auto the response looks normal; compare input_tokens with what you sent."""
    return usage_input_tokens / requested_tokens


# Recorded on 2026-11-11 against a local Ollama 0.40.16 with qwen2.5:1.5b (default 4096 context).
# One run per mode; a synthetic 58,203-character help-desk log of 900 CASE lines plus a question.
RECORDED = {
    'responses_omitted': {'status': 400, 'error': {'message': 'request (27599 tokens) exceeds the available context size (4096 tokens), try increasing it', 'type': 'invalid_request_error'}},
    'responses_disabled': {'status': 400, 'error': {'message': 'request (27599 tokens) exceeds the available context size (4096 tokens), try increasing it', 'type': 'invalid_request_error'}},
    'responses_auto': {'status': 200, 'response_status': 'completed', 'usage': {'input_tokens': 2050, 'output_tokens': 2}},
    'chat_omitted': {'status': 200, 'prompt_eval_count': 2050},
    'chat_truncate_false': {'status': 400, 'error': 'request (27599 tokens) exceeds the available context size (4096 tokens), try increasing it'},
}


def live():
    base = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434')
    model = os.environ.get('OLLAMA_MODEL', 'qwen2.5:1.5b')
    lines = [f'CASE-{4100 + i}: order BK-{9000 + i} for Geetha, status note {i}, shelf C{i % 40}.' for i in range(900)]
    text = '\n'.join(lines + ['Final line: reply with only the word READY.'])
    for mode in ('disabled', 'auto'):
        req = urllib.request.Request(base + '/v1/responses', json.dumps(request_body(model, text, mode, 8)).encode(), {'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                data = json.loads(r.read())
                print(mode, r.status, data.get('status'), data.get('usage'))
        except urllib.error.HTTPError as e:
            body = json.loads(e.read() or b'{}')
            print(mode, e.code, overflow(e.code, body), body.get('error', {}).get('message'))


if __name__ == '__main__':
    if '--live' in sys.argv:
        live()
    else:
        for k, v in RECORDED.items():
            print(k, v['status'], overflow(v['status'], v))
