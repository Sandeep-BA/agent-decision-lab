# Author: Sandeep Belgavi. Verify symmetric webhook signatures in the Standard Webhooks style
# (v1, HMAC-SHA256 over "msg_id.timestamp.payload", base64). Synthetic secret and events for the
# fictional Belgavi's Book Store; standard library only; nothing is sent over a network.
"""Run: python verify.py"""
import base64
import hashlib
import hmac
import json
import time

TOLERANCE_SECONDS = 300


def sign(secret: bytes, msg_id: str, timestamp: int, body: bytes) -> str:
    content = msg_id.encode() + b'.' + str(timestamp).encode() + b'.' + body
    return 'v1,' + base64.b64encode(hmac.new(secret, content, hashlib.sha256).digest()).decode()


class Verifier:
    def __init__(self, secrets, now=time.time, tolerance=TOLERANCE_SECONDS):
        self.secrets, self.now, self.tolerance = list(secrets), now, tolerance
        self.seen = {}  # msg_id -> first accepted time; keep at least as long as the tolerance

    def verify(self, headers: dict, raw_body: bytes) -> str:
        msg_id, ts, sigs = headers.get('webhook-id', ''), headers.get('webhook-timestamp', ''), headers.get('webhook-signature', '')
        if not msg_id or '.' in msg_id or not ts.isdigit():
            return 'reject: malformed headers'
        ts_int = int(ts)
        if abs(self.now() - ts_int) > self.tolerance:
            return 'reject: timestamp outside tolerance'
        offered = [s.split(',', 1)[1] for s in sigs.split(' ') if s.startswith('v1,')]
        expected = [sign(k, msg_id, ts_int, raw_body).split(',', 1)[1] for k in self.secrets]
        if not any(hmac.compare_digest(o.encode(), e.encode()) for o in offered for e in expected):
            return 'reject: no matching signature'
        if msg_id in self.seen:
            return 'duplicate: already processed'
        self.seen[msg_id] = self.now()
        return 'accept'

    def expire(self):
        cutoff = self.now() - 2 * self.tolerance
        self.seen = {k: t for k, t in self.seen.items() if t >= cutoff}


def reserialize(raw_body: bytes) -> bytes:
    """What a framework that parses JSON before the handler effectively hands back."""
    return json.dumps(json.loads(raw_body)).encode()


def run():
    old, new = b'synthetic-old-secret-32-bytes-0001', b'synthetic-new-secret-32-bytes-0002'
    clock = [1795000000]
    v = Verifier([old, new], now=lambda: clock[0])
    raw = '{"type":"order.refunded","case":"CASE-4301","customer":"Geetha","note":"Café edition"}'.encode()
    h = {'webhook-id': 'msg_4301a', 'webhook-timestamp': str(clock[0]), 'webhook-signature': sign(new, 'msg_4301a', clock[0], raw)}
    out = {'raw_body': v.verify(h, raw)}
    out['redelivery_same_id'] = v.verify(h, raw)
    h2 = dict(h, **{'webhook-id': 'msg_4301b', 'webhook-signature': sign(new, 'msg_4301b', clock[0], raw)})
    out['reserialized_body'] = v.verify(h2, reserialize(raw))
    out['reserialized_bytes'] = [len(raw), len(reserialize(raw))]
    h3 = {'webhook-id': 'msg_4302', 'webhook-timestamp': str(clock[0]), 'webhook-signature': sign(old, 'msg_4302', clock[0], raw)}
    out['old_secret_during_rotation'] = v.verify(h3, raw)
    tampered = raw.replace(b'CASE-4301', b'CASE-4999')
    h4 = dict(h3, **{'webhook-id': 'msg_4303', 'webhook-signature': sign(old, 'msg_4303', clock[0], raw)})
    out['tampered_body'] = v.verify(h4, tampered)
    clock[0] += 301
    h5 = {'webhook-id': 'msg_4304', 'webhook-timestamp': str(clock[0] - 301), 'webhook-signature': sign(new, 'msg_4304', clock[0] - 301, raw)}
    out['captured_and_replayed_301s_later'] = v.verify(h5, raw)
    out['dot_in_id'] = v.verify({'webhook-id': 'a.b', 'webhook-timestamp': str(clock[0]), 'webhook-signature': 'v1,x'}, raw)
    return out


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
