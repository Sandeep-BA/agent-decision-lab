"""Overlapping chunks and top-k context: measure the repeated text, then merge hits by source span.
Author: Sandeep Belgavi.

Synthetic help articles for the fictional Belgavi's Book Store are split into fixed-size character
windows with overlap. A deterministic lexical scorer stands in for a retriever, so every number is
reproducible. Standard library only; no embedding model or vector database is used.
"""
from collections import defaultdict
import json, math, re, sys

DOCS = {
    'returns-policy': [
        'Books can be returned within 30 days of delivery for a full refund to the original payment method.',
        'A damaged book should be reported with a photo of the damage and the packing slip.',
        'For a damaged book the store sends a replacement or a refund, whichever the customer chooses.',
        'Refunds for a returned book are issued after the warehouse receives and inspects the parcel.',
        'Inspection normally finishes two working days after the parcel arrives at the warehouse.',
        'A refund for a damaged book does not require the book to be sent back when the photo shows the damage clearly.',
        'Gift orders are refunded to the person who paid, not to the recipient of the gift.',
        'Return labels are emailed once the help desk approves the return request.',
        'Books marked final sale cannot be returned unless they arrive damaged.',
        'Partial refunds apply when only some books in an order are returned.',
        'Shipping charges are refunded only when the return is caused by a store error or a damaged book.',
        'Customers can track the refund status from the order page once the return is approved.',
    ],
    'shipping-guide': [
        'Standard delivery takes three to five working days within the country.',
        'Express delivery arrives in one to two working days for an extra charge shown at checkout.',
        'A parcel that arrives damaged should be photographed before it is opened further.',
        'Tracking numbers are sent by email when the parcel leaves the warehouse.',
        'Delivery addresses can be changed until the parcel is handed to the courier.',
        'Parcels returned to the warehouse as undeliverable are refunded minus the shipping charge.',
        'Large orders may arrive in more than one parcel, each with its own tracking number.',
        'The courier attempts delivery twice before the parcel returns to the local depot.',
    ],
    'gift-cards': [
        'Gift cards never expire and can be used for any book in the store.',
        'A gift card cannot be refunded or exchanged for cash.',
        'When an order paid with a gift card is refunded, the amount goes back to the gift card.',
        'Lost gift card codes can be reissued by the help desk with proof of purchase.',
        'Gift cards can be combined with one discount code per order.',
    ],
    'damaged-items-checklist': [
        'Before approving a damaged book claim, the help desk checks the photo, the order number and the delivery date.',
        'Claims for a damaged book made more than 30 days after delivery go to a person for review.',
        'A replacement is sent only when the same edition is in stock; otherwise a refund is issued.',
        'Repeated damage on the same delivery route is reported to the courier.',
    ],
}
QUERY = 'refund for a damaged book that was returned'
CHUNK, OVERLAP, K = 360, 120, 6


def chunk(doc_id, text, size=CHUNK, overlap=OVERLAP):
    """Fixed character windows, moved back to the previous space so words are not cut."""
    out, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = text.rfind(' ', start + size // 2, end)
            end = cut if cut > start else end
        out.append({'doc': doc_id, 'start': start, 'end': end, 'text': text[start:end]})
        if end >= len(text):
            break
        nxt = end - overlap
        sp = text.find(' ', nxt)
        start = sp + 1 if 0 <= sp < end else nxt
    return out


def tokens(s):
    return re.findall(r'[a-z0-9]+', s.lower())


STOP = {'a', 'for', 'that', 'was', 'the', 'to', 'of', 'and', 'or', 'is', 'be', 'when', 'by', 'an', 'it'}


def score(query, text):
    q = [t for t in tokens(query) if t not in STOP]
    words = tokens(text)
    hits = sum(words.count(t) for t in q)
    return round(hits / math.sqrt(len(words) or 1), 4)


def build_index():
    chunks = []
    for doc_id, sentences in DOCS.items():
        chunks.extend(chunk(doc_id, ' '.join(sentences)))
    return chunks


def ranked(chunks, query=QUERY):
    scored = [dict(c, score=score(query, c['text'])) for c in chunks]
    return sorted(scored, key=lambda c: (-c['score'], c['doc'], c['start']))


def unique_chars(passages):
    spans = defaultdict(list)
    for p in passages:
        spans[p['doc']].append((p['start'], p['end']))
    total = 0
    for doc, ss in spans.items():
        ss.sort(); cur_s, cur_e = ss[0]
        for s, e in ss[1:]:
            if s <= cur_e:
                cur_e = max(cur_e, e)
            else:
                total += cur_e - cur_s; cur_s, cur_e = s, e
        total += cur_e - cur_s
    return total


def merge_spans(hits):
    """Merge hits from the same document whose spans overlap or touch; keep the best score."""
    by_doc = defaultdict(list)
    for h in hits:
        by_doc[h['doc']].append(h)
    merged = []
    for doc, hs in by_doc.items():
        hs.sort(key=lambda h: h['start'])
        cur = dict(hs[0], parts=1)
        for h in hs[1:]:
            if h['start'] <= cur['end']:
                cur['end'] = max(cur['end'], h['end']); cur['score'] = max(cur['score'], h['score']); cur['parts'] += 1
            else:
                merged.append(cur); cur = dict(h, parts=1)
        merged.append(cur)
    text = {d: ' '.join(s) for d, s in DOCS.items()}
    for m in merged:
        m['text'] = text[m['doc']][m['start']:m['end']]
    return sorted(merged, key=lambda m: (-m['score'], m['doc'], m['start']))


def fill(ranking, budget, merge=True, pool=4):
    """Fill a character budget. With merge, take a deeper candidate pool, merge spans, then fill."""
    if not merge:
        picked = ranking[:K]
        return picked, sum(len(p['text']) for p in picked)
    candidates = merge_spans(ranking[:K * pool])
    picked, used = [], 0
    for m in candidates:
        if used + len(m['text']) <= budget:
            picked.append(m); used += len(m['text'])
    return picked, used


def summarize(passages, used):
    return {'passages': len(passages), 'chars_in_context': used, 'unique_chars': unique_chars(passages),
            'repeated_share': round(1 - unique_chars(passages) / used, 3) if used else 0.0,
            'documents': sorted({p['doc'] for p in passages}),
            'spans': [[p['doc'], p['start'], p['end'], p['score']] for p in passages]}


def exact_text_dedup(passages):
    return len({p['text'] for p in passages})


def main():
    chunks = build_index()
    ranking = ranked(chunks)
    plain, used_plain = fill(ranking, budget=None, merge=False)
    merged, used_merged = fill(ranking, budget=used_plain, merge=True)
    report = {
        'chunk_size': CHUNK, 'overlap': OVERLAP, 'k': K, 'query': QUERY, 'chunks_indexed': len(chunks),
        'plain_top_k': summarize(plain, used_plain),
        'exact_text_dedup_keeps': exact_text_dedup(plain),
        'span_merged_same_budget': summarize(merged, used_merged),
    }
    json.dump(report, sys.stdout, indent=2); print()
    return report


if __name__ == '__main__':
    main()
