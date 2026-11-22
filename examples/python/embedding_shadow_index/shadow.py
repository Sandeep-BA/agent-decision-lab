# Author: Sandeep Belgavi. Shadow-index comparison of two embedding functions over synthetic
# help articles for the fictional Belgavi's Book Store. Two small deterministic embedders stand in
# for an old and a new model; no model or network calls. Standard library only.
"""Run: python shadow.py"""
import hashlib
import json
import math
import re

DIMS = 64
DOCS = {
    'D01': 'How to return a book you ordered online within 30 days',
    'D02': 'Refund timing after we receive your returned book',
    'D03': 'Change the delivery address on an order that has not shipped',
    'D04': 'Track your order and see the courier status',
    'D05': 'Cancel an order before it is packed',
    'D06': 'Gift cards: balance, expiry and how to redeem',
    'D07': 'Damaged or misprinted book: request a replacement',
    'D08': 'Preorder a book that is not yet published',
    'D09': 'Membership points and how they are calculated',
    'D10': 'Reset your account password',
    'D11': 'Update the email address on your account',
    'D12': 'Pay with a saved card or change the payment method',
    'D13': 'Invoice and tax receipt for a business purchase',
    'D14': 'Ebook download limits and supported devices',
    'D15': 'Audiobook playback stops or will not download',
    'D16': 'Bulk orders for schools and libraries',
}
QUERIES = [  # (query, relevant ids, class)
    ('return a book', {'D01'}, 'clean'), ('refund after return', {'D02'}, 'clean'),
    ('change delivery address', {'D03'}, 'clean'), ('cancel my order', {'D05'}, 'clean'),
    ('gift card balance', {'D06'}, 'clean'), ('reset password', {'D10'}, 'clean'),
    ('ebook download limit', {'D14'}, 'clean'), ('bulk order for a school', {'D16'}, 'clean'),
    ('retrun a bok', {'D01'}, 'typo'), ('refnd aftr retrn', {'D02'}, 'typo'),
    ('chnage delivry adress', {'D03'}, 'typo'), ('cancle my ordr', {'D05'}, 'typo'),
    ('gift crad balanse', {'D06'}, 'typo'), ('rest pasword', {'D10'}, 'typo'),
    ('ebok downlod limt', {'D14'}, 'typo'), ('bulk oders for a scool', {'D16'}, 'typo'),
]


def _bucket(token):
    h = hashlib.sha256(token.encode()).digest()
    return h[0] % DIMS, 1.0 if h[1] % 2 else -1.0


def _norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def embed_words(text):  # the "old" model: hashed bag of words
    v = [0.0] * DIMS
    for w in re.findall(r'[a-z]+', text.lower()):
        i, s = _bucket('w:' + w); v[i] += s
    return _norm(v)


def embed_trigrams(text):  # the "new" model: hashed character trigrams
    v = [0.0] * DIMS
    for w in re.findall(r'[a-z]+', text.lower()):
        w = f' {w} '
        for j in range(len(w) - 2):
            i, s = _bucket('t:' + w[j:j + 3]); v[i] += s
    return _norm(v)


def top_k(qvec, index, k):
    scored = sorted(((sum(a * b for a, b in zip(qvec, dv)), d) for d, dv in index.items()), key=lambda t: (-t[0], t[1]))
    return [d for _, d in scored[:k]]


def evaluate(k=3):
    old = {d: embed_words(t) for d, t in DOCS.items()}
    new = {d: embed_trigrams(t) for d, t in DOCS.items()}
    per_class = {}
    for q, rel, cls in QUERIES:
        a, b = top_k(embed_words(q), old, k), top_k(embed_trigrams(q), new, k)
        mixed = top_k(embed_trigrams(q), old, k)  # new query vector against old document vectors
        c = per_class.setdefault(cls, {'queries': 0, 'old_hits': 0, 'new_hits': 0, 'mixed_hits': 0, 'overlap_sum': 0})
        c['queries'] += 1
        c['old_hits'] += bool(rel & set(a)); c['new_hits'] += bool(rel & set(b)); c['mixed_hits'] += bool(rel & set(mixed))
        c['overlap_sum'] += len(set(a) & set(b))
    for c in per_class.values():
        c['mean_overlap_at_k'] = round(c.pop('overlap_sum') / (c['queries'] * k), 2)
    return per_class


def cutover_plan(per_class, min_gain=0):
    """Per query class: switch only where labelled recall on the new index is at least as good."""
    return {cls: ('new' if c['new_hits'] - c['old_hits'] >= min_gain and c['new_hits'] >= c['old_hits'] else 'old')
            for cls, c in per_class.items()}


if __name__ == '__main__':
    r = evaluate()
    print(json.dumps({'k': 3, 'per_class': r, 'plan': cutover_plan(r)}, indent=2))
