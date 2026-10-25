"""OpenAI-compatible Chat Completions conformance checks.

Author: Sandeep Belgavi. Standard library only.

Sends a fixed set of small requests to any server that claims the OpenAI Chat Completions
shape (`POST {base}/chat/completions`) and reports, per check, PASS, DIFF (the server answered
but not with the effect the check expects) or FAIL (error or unusable answer). `unknown_param` is a
strictness check and `seed` is informational: OpenAI documents seed determinism as best effort.
The point is to find out what a "compatible" endpoint silently ignores before your code
depends on it.

Usage:
  python conformance.py --base-url http://127.0.0.1:11434/v1 --model qwen2.5:0.5b-instruct
  python conformance.py --base-url http://127.0.0.1:8899/v1 --model fake   # against fake_server.py
Environment: OPENAI_COMPAT_API_KEY is sent as a Bearer token if set (never printed).
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

FINISH = {'stop', 'length', 'tool_calls', 'content_filter'}
WEATHER_TOOL = {
    'type': 'function',
    'function': {
        'name': 'get_weather',
        'description': 'Current temperature for a city.',
        'parameters': {'type': 'object', 'properties': {'city': {'type': 'string'}},
                       'required': ['city'], 'additionalProperties': False},
    },
}


class Client:
    def __init__(self, base_url, model, timeout=120):
        self.base, self.model, self.timeout = base_url.rstrip('/'), model, timeout
        self.key = os.environ.get('OPENAI_COMPAT_API_KEY', '')

    def post(self, body, stream=False):
        """Return (status, parsed JSON or list of SSE data payloads)."""
        body = dict(body)
        body.setdefault('model', self.model)
        data = json.dumps(body).encode()
        req = urllib.request.Request(self.base + '/chat/completions', data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        if self.key:
            req.add_header('Authorization', 'Bearer ' + self.key)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode('utf-8')
                status = resp.status
        except urllib.error.HTTPError as e:
            raw, status = e.read().decode('utf-8', 'replace'), e.code
        if stream and status == 200:
            events = [line[5:].strip() for line in raw.splitlines() if line.startswith('data:')]
            return status, events
        try:
            return status, json.loads(raw)
        except ValueError:
            return status, {'_unparsed': raw[:200]}


def msg(text):
    return [{'role': 'user', 'content': text}]


def check_shape(c):
    s, r = c.post({'messages': msg('Reply with the single word: ready'), 'max_tokens': 20, 'temperature': 0})
    if s != 200:
        return 'FAIL', 'HTTP %s' % s
    ch = (r.get('choices') or [{}])[0]
    missing = [k for k in ('id', 'object', 'created', 'choices', 'usage') if k not in r]
    if missing or ch.get('message', {}).get('role') != 'assistant' or ch.get('finish_reason') not in FINISH:
        return 'DIFF', 'missing %s, finish_reason=%r' % (missing, ch.get('finish_reason'))
    u = r['usage']
    if u.get('total_tokens') != u.get('prompt_tokens', 0) + u.get('completion_tokens', 0):
        return 'DIFF', 'usage does not add up: %s' % u
    return 'PASS', 'object=%s finish_reason=%s usage=%s' % (r['object'], ch['finish_reason'], u)


def check_length(c):
    s, r = c.post({'messages': msg('Count from 1 to 50 separated by spaces.'), 'max_tokens': 5, 'temperature': 0})
    if s != 200:
        return 'FAIL', 'HTTP %s' % s
    fr = r['choices'][0].get('finish_reason')
    return ('PASS' if fr == 'length' else 'DIFF'), 'finish_reason=%r with max_tokens=5' % fr


def check_max_completion_tokens(c):
    s, r = c.post({'messages': msg('Count from 1 to 50 separated by spaces.'), 'max_completion_tokens': 5, 'temperature': 0})
    if s != 200:
        return 'FAIL', 'HTTP %s: %s' % (s, str(r)[:120])
    ct = r.get('usage', {}).get('completion_tokens')
    fr = r['choices'][0].get('finish_reason')
    ok = fr == 'length' and ct is not None and ct <= 5
    return ('PASS' if ok else 'DIFF'), 'finish_reason=%r completion_tokens=%r with max_completion_tokens=5' % (fr, ct)


def check_n(c):
    s, r = c.post({'messages': msg('Name a colour.'), 'n': 2, 'max_tokens': 5, 'temperature': 1})
    if s != 200:
        return 'FAIL', 'HTTP %s: %s' % (s, str(r)[:120])
    k = len(r.get('choices', []))
    return ('PASS' if k == 2 else 'DIFF'), 'asked n=2, got %d choice(s)' % k


def check_stop(c):
    s, r = c.post({'messages': msg('Write the letters A B C D E F separated by spaces.'), 'stop': ['D'],
                   'max_tokens': 30, 'temperature': 0})
    if s != 200:
        return 'FAIL', 'HTTP %s' % s
    text = r['choices'][0]['message'].get('content') or ''
    fr = r['choices'][0].get('finish_reason')
    ok = 'D' not in text and fr == 'stop'
    return ('PASS' if ok else 'DIFF'), 'content=%r finish_reason=%r' % (text[:40], fr)


def check_json_object(c):
    s, r = c.post({'messages': msg('Return a JSON object with key "city" set to "Pune".'),
                   'response_format': {'type': 'json_object'}, 'max_tokens': 40, 'temperature': 0})
    if s != 200:
        return 'FAIL', 'HTTP %s: %s' % (s, str(r)[:120])
    text = r['choices'][0]['message'].get('content') or ''
    try:
        obj = json.loads(text)
    except ValueError:
        return 'DIFF', 'content is not JSON: %r' % text[:60]
    return 'PASS', 'parsed JSON keys %s' % sorted(obj)[:5]


def check_json_schema(c):
    schema = {'type': 'object', 'properties': {'city': {'type': 'string'}, 'celsius': {'type': 'integer'}},
              'required': ['city', 'celsius'], 'additionalProperties': False}
    s, r = c.post({'messages': msg('Give a city and a temperature.'), 'max_tokens': 60, 'temperature': 0,
                   'response_format': {'type': 'json_schema', 'json_schema': {'name': 'reading', 'strict': True, 'schema': schema}}})
    if s != 200:
        return 'FAIL', 'HTTP %s: %s' % (s, str(r)[:120])
    text = r['choices'][0]['message'].get('content') or ''
    try:
        obj = json.loads(text)
    except ValueError:
        return 'DIFF', 'content is not JSON: %r' % text[:60]
    ok = set(obj) == {'city', 'celsius'} and isinstance(obj.get('celsius'), int) and isinstance(obj.get('city'), str)
    return ('PASS' if ok else 'DIFF'), 'object=%s' % json.dumps(obj)[:80]


def check_tool_call(c):
    s, r = c.post({'messages': msg('What is the weather in Pune? Use the tool.'), 'tools': [WEATHER_TOOL],
                   'tool_choice': {'type': 'function', 'function': {'name': 'get_weather'}}, 'max_tokens': 60, 'temperature': 0})
    if s != 200:
        return 'FAIL', 'HTTP %s: %s' % (s, str(r)[:120])
    ch = r['choices'][0]
    calls = ch['message'].get('tool_calls') or []
    if not calls:
        return 'DIFF', 'no tool_calls; finish_reason=%r' % ch.get('finish_reason')
    fn = calls[0].get('function', {})
    args = fn.get('arguments')
    problems = []
    if not isinstance(args, str):
        problems.append('arguments is %s, not a JSON string' % type(args).__name__)
    else:
        try:
            json.loads(args)
        except ValueError:
            problems.append('arguments string is not JSON')
    if not calls[0].get('id'):
        problems.append('missing tool call id')
    if ch.get('finish_reason') != 'tool_calls':
        problems.append('finish_reason=%r' % ch.get('finish_reason'))
    return ('DIFF' if problems else 'PASS'), ('; '.join(problems) or 'name=%s arguments=%s' % (fn.get('name'), args))


def check_stream(c):
    s, events = c.post({'messages': msg('Say hi.'), 'max_tokens': 10, 'temperature': 0, 'stream': True,
                        'stream_options': {'include_usage': True}}, stream=True)
    if s != 200 or not isinstance(events, list):
        return 'FAIL', 'HTTP %s' % s
    done = bool(events) and events[-1] == '[DONE]'
    chunks = [json.loads(e) for e in events if e != '[DONE]']
    usage = [ch for ch in chunks if ch.get('usage')]
    final_usage_empty_choices = bool(usage) and usage[-1].get('choices') == []
    ok = done and usage and final_usage_empty_choices
    return ('PASS' if ok else 'DIFF'), '%d chunks, [DONE]=%s, usage chunk=%s, usage chunk has empty choices=%s' % (
        len(chunks), done, bool(usage), final_usage_empty_choices)


def check_logprobs(c):
    s, r = c.post({'messages': msg('Say yes.'), 'max_tokens': 3, 'temperature': 0, 'logprobs': True, 'top_logprobs': 2})
    if s != 200:
        return 'FAIL', 'HTTP %s: %s' % (s, str(r)[:120])
    lp = r['choices'][0].get('logprobs')
    content = (lp or {}).get('content') if isinstance(lp, dict) else None
    return ('PASS' if content else 'DIFF'), 'logprobs present=%s' % bool(content)


def check_unknown_param(c):
    s, r = c.post({'messages': msg('Say ok.'), 'max_tokens': 3, 'frobnicate_level': 3})
    return ('PASS' if s == 400 else 'DIFF'), 'unknown parameter -> HTTP %s (a strict server answers 400; 200 means it was silently ignored)' % s


def check_bad_model(c):
    s, r = c.post({'model': 'no-such-model-xyz', 'messages': msg('hi'), 'max_tokens': 3})
    err = r.get('error') if isinstance(r, dict) else None
    shape = isinstance(err, dict) and 'message' in err
    ok = s == 404 and shape
    return ('PASS' if ok else 'DIFF'), 'HTTP %s, error object=%s, keys=%s' % (s, shape, sorted(err)[:4] if isinstance(err, dict) else None)


def check_seed(c):
    body = {'messages': msg('Invent a one-line product name.'), 'max_tokens': 12, 'temperature': 1, 'seed': 42}
    a = c.post(body)[1]
    b = c.post(body)[1]
    try:
        ta, tb = a['choices'][0]['message']['content'], b['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        return 'FAIL', 'unusable response'
    return ('PASS' if ta == tb else 'DIFF'), 'informational: same seed twice gave %s output' % ('identical' if ta == tb else 'different')


CHECKS = [check_shape, check_length, check_max_completion_tokens, check_n, check_stop, check_json_object,
          check_json_schema, check_tool_call, check_stream, check_logprobs, check_unknown_param, check_bad_model, check_seed]


def run(base_url, model):
    c = Client(base_url, model)
    results = []
    for chk in CHECKS:
        try:
            verdict, detail = chk(c)
        except Exception as e:  # a crash in one check must not hide the others
            verdict, detail = 'FAIL', '%s: %s' % (type(e).__name__, e)
        results.append({'check': chk.__name__[6:], 'verdict': verdict, 'detail': detail})
    return results


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--base-url', required=True)
    ap.add_argument('--model', required=True)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    results = run(args.base_url, args.model)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print('%-22s %-4s  %s' % (r['check'], r['verdict'], r['detail']))
    counts = {v: sum(r['verdict'] == v for r in results) for v in ('PASS', 'DIFF', 'FAIL')}
    print('summary', counts, file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
