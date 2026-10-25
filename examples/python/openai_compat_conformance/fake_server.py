"""A tiny fake Chat Completions server with two behaviour profiles, for offline tests.

Author: Sandeep Belgavi. Standard library only. The replies are canned text, not model output.

- strict:  behaves like the reference in every check the suite makes (honours both limit fields, n,
           rejects unknown parameters with 400, is deterministic for a seed).
- lenient: reproduces the DIFFs recorded against Ollama 0.40.6 on 2026-10-25 (ignores
           max_completion_tokens and n, accepts unknown parameters, first seeded reply differs).

Run: python fake_server.py --profile lenient --port 8899
"""
import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KNOWN = {'model', 'messages', 'max_tokens', 'max_completion_tokens', 'n', 'stop', 'stream', 'stream_options',
         'temperature', 'top_p', 'seed', 'response_format', 'tools', 'tool_choice', 'logprobs', 'top_logprobs'}
LONG = ' '.join(str(i) for i in range(1, 51))


def make_handler(profile):
    state = {'seed_calls': 0}
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send_json(self, status, body):
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
            if self.path.rstrip('/') != '/v1/chat/completions':
                return self.send_json(404, {'error': {'message': 'not found', 'type': 'invalid_request_error', 'param': None, 'code': None}})
            if body.get('model') == 'no-such-model-xyz':
                return self.send_json(404, {'error': {'message': 'model not found', 'type': 'api_error', 'param': None, 'code': None}})
            unknown = set(body) - KNOWN
            if unknown and profile == 'strict':
                return self.send_json(400, {'error': {'message': 'Unrecognized request argument: %s' % sorted(unknown)[0],
                                                      'type': 'invalid_request_error', 'param': sorted(unknown)[0], 'code': None}})
            prompt = body['messages'][-1]['content']
            limit = body.get('max_tokens')
            if limit is None and profile == 'strict':
                limit = body.get('max_completion_tokens')
            if 'Count from 1 to 50' in prompt:
                words = LONG.split()
                text = ' '.join(words[:limit]) if limit else LONG
                finish = 'length' if limit and limit < len(words) else 'stop'
            elif 'letters A B C D E F' in prompt:
                text, finish = 'A B C ', 'stop'
            elif 'JSON object' in prompt:
                text, finish = '{"city": "Pune"}', 'stop'
            elif body.get('response_format', {}).get('type') == 'json_schema':
                text, finish = '{"city": "Pune", "celsius": 24}', 'stop'
            elif 'product name' in prompt:
                with lock:
                    state['seed_calls'] += 1
                    first = state['seed_calls'] == 1
                text = 'QuantumCraft' if (profile == 'lenient' and first) else 'QuantumLeap'
                finish = 'stop'
            else:
                text, finish = 'ready', 'stop'
            completion_tokens = len(text.split()) or 1
            message = {'role': 'assistant', 'content': text}
            if body.get('tool_choice'):
                message = {'role': 'assistant', 'content': None, 'tool_calls': [{
                    'id': 'call_1', 'type': 'function',
                    'function': {'name': 'get_weather', 'arguments': '{"city":"Pune"}'}}]}
                finish = 'tool_calls'
            n = body.get('n', 1) if profile == 'strict' else 1
            choice = lambda i: {'index': i, 'message': message, 'finish_reason': finish,
                                'logprobs': {'content': [{'token': 'yes', 'logprob': -0.01, 'top_logprobs': []}]} if body.get('logprobs') else None}
            usage = {'prompt_tokens': 20, 'completion_tokens': completion_tokens, 'total_tokens': 20 + completion_tokens}
            if body.get('stream'):
                chunks = [{'id': 'c1', 'object': 'chat.completion.chunk', 'choices': [{'index': 0, 'delta': {'content': w + ' '}, 'finish_reason': None}]}
                          for w in text.split()]
                chunks.append({'id': 'c1', 'object': 'chat.completion.chunk', 'choices': [{'index': 0, 'delta': {}, 'finish_reason': finish}]})
                if (body.get('stream_options') or {}).get('include_usage'):
                    chunks.append({'id': 'c1', 'object': 'chat.completion.chunk', 'choices': [], 'usage': usage})
                data = ''.join('data: %s\n\n' % json.dumps(c) for c in chunks) + 'data: [DONE]\n\n'
                raw = data.encode()
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                return self.wfile.write(raw)
            self.send_json(200, {'id': 'chatcmpl-1', 'object': 'chat.completion', 'created': 1792900000,
                                 'model': body.get('model'), 'choices': [choice(i) for i in range(n)], 'usage': usage})

    return Handler


def serve(profile, port=0):
    """Start in a background thread; return (server, base_url)."""
    server = ThreadingHTTPServer(('127.0.0.1', port), make_handler(profile))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, 'http://127.0.0.1:%d/v1' % server.server_address[1]


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--profile', choices=['strict', 'lenient'], default='lenient')
    ap.add_argument('--port', type=int, default=8899)
    a = ap.parse_args()
    srv, url = serve(a.profile, a.port)
    print('serving %s profile at %s (Ctrl+C to stop)' % (a.profile, url))
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        srv.shutdown()
