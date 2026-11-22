# Author: Sandeep Belgavi. JSON-RPC ids are chosen by each sender, so a client and a server can
# both use id 7. This model shows what happens when the body of an HTTP response to a client's
# *reply* POST is dispatched by id alone, and the rule from openai/codex PR 63075 (merged
# 2026-11-22): a reply POST must be acknowledged with 202 or 204, and anything else is an error.
# Synthetic messages; no MCP server, SDK or network is used.
"""Run: python correlate.py"""
import json

ACK = {202, 204}


def kind(msg):
    if 'method' in msg:
        return 'request' if 'id' in msg else 'notification'
    return 'error' if 'error' in msg else 'result'


class Client:
    def __init__(self, strict):
        self.strict, self.pending, self.resolved, self.log = strict, {}, {}, []

    def send_request(self, rid, method):
        self.pending[rid] = method
        self.log.append(f'sent request id {rid} ({method}); pending {sorted(self.pending)}')

    def _dispatch(self, msg, via):
        k = kind(msg)
        if k in ('result', 'error'):
            rid = msg.get('id')
            if rid in self.pending:
                self.resolved[rid] = (k, msg.get('error', msg.get('result')), via)
                del self.pending[rid]
                self.log.append(f'{via}: {k} id {rid} resolved our pending request')
            else:
                self.log.append(f'{via}: {k} id {rid} matches nothing pending; dropped')

    def post_reply(self, reply, status, body):
        """POST our reply to the server's request; then handle the HTTP response."""
        self.log.append(f'POST reply id {reply["id"]} -> HTTP {status}' + (f' with {kind(body)} id {body.get("id")}' if body else ' (no body)'))
        if status in ACK:
            return 'acknowledged'
        if self.strict:
            self.log.append('strict: a reply POST must be acknowledged; body not decoded')
            return f'error: expected acknowledgement, got HTTP {status}'
        if body:
            self._dispatch(body, via=f'body of reply POST (HTTP {status})')
        return 'dispatched'

    def response_to_request(self, msg):
        self._dispatch(msg, via='response to our request POST')


def scenario(strict, status=409):
    c = Client(strict)
    c.send_request(7, 'tools/call')
    server_request = {'jsonrpc': '2.0', 'id': 7, 'method': 'elicitation/create'}
    c.log.append(f'server sent its own request id {server_request["id"]} ({server_request["method"]})')
    reply = {'jsonrpc': '2.0', 'id': 7, 'result': {'action': 'accept'}}
    rejection = {'jsonrpc': '2.0', 'id': 7, 'error': {'code': -32600, 'message': 'unknown request'}}
    body = None if status in ACK else rejection
    outcome = c.post_reply(reply, status, body)
    c.response_to_request({'jsonrpc': '2.0', 'id': 7, 'result': {'content': [{'type': 'text', 'text': 'Order BK-7 found'}]}})
    got = c.resolved.get(7)
    return {'strict': strict, 'status': status, 'reply_outcome': outcome,
            'request_7_resolved_with': got[0] if got else None,
            'request_7_resolved_via': got[2] if got else None, 'log': c.log}


def run():
    return {f'{"strict" if s else "naive"}_{st}': scenario(s, st) for s in (False, True) for st in (409, 200, 202, 204)}


if __name__ == '__main__':
    for k, v in run().items():
        print(k, v['reply_outcome'], '| request 7 ->', v['request_7_resolved_with'], 'via', v['request_7_resolved_via'])
