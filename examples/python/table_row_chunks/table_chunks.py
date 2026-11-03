"""Three ways to chunk the same tables, BM25 retrieval, and a strict check that the retrieved text carries the
row, the column header and the cell a question needs.

Author: Sandeep Belgavi. Companion to "Tables in a Retrieval Corpus" (aicassindra.com).
Synthetic Belgavi's Book Store corpus; standard library only; no model or embedding service is called.
Usage: python table_chunks.py"""
import math, re
from collections import Counter

TABLES = [
 ('Returns policy: return rules by item type', ['Item type', 'Return window', 'Refund method', 'Restocking fee'], [
   ['Paperback', '30 days', 'Original payment or store credit', 'None'],
   ['Hardcover', '30 days', 'Original payment or store credit', 'None'],
   ['Signed edition', '7 days', 'Store credit only', '10 percent'],
   ['Box set', '14 days', 'Original payment', '5 percent'],
   ['E-book', 'Not returnable', 'Not applicable', 'Not applicable'],
   ['Gift card', 'Not returnable', 'Not applicable', 'Not applicable']]),
 ('Shipping: delivery times by destination', ['Destination', 'Standard delivery', 'Express delivery', 'Express fee'], [
   ['Same city', '2 days', 'Next day', '40 rupees'],
   ['Same state', '4 days', '2 days', '60 rupees'],
   ['Other states', '7 days', '3 days', '90 rupees'],
   ['Remote areas', '10 days', 'Not available', 'Not applicable']]),
 ('Membership: benefits by tier', ['Tier', 'Discount', 'Free shipping', 'Early access'], [
   ['Reader', '5 percent', 'Orders above 499 rupees', 'No'],
   ['Collector', '10 percent', 'All orders', 'Signed editions 48 hours early'],
   ['Patron', '15 percent', 'All orders', 'All preorders 7 days early']]),
]
PROSE = [
 'Returns policy. Books must be in the condition they were delivered in. Start a return from the order page; a return label is emailed within one day.',
 'Shipping. Orders are packed within one working day. Tracking numbers are sent by email once the parcel leaves the store.',
 'Membership. Membership renews every year. Discounts do not apply to gift cards.',
]
# question, row key, column header the answer sits under, expected cell
QUESTIONS = [
 ('How many days do I have to return a signed edition?', 'Signed edition', 'Return window', '7 days'),
 ('Is there a restocking fee on a box set return?', 'Box set', 'Restocking fee', '5 percent'),
 ('Can I get my money back on a signed edition or only credit?', 'Signed edition', 'Refund method', 'Store credit only'),
 ('How long does standard delivery take to other states?', 'Other states', 'Standard delivery', '7 days'),
 ('What does express delivery cost in the same state?', 'Same state', 'Express fee', '60 rupees'),
 ('Is express shipping available to remote areas?', 'Remote areas', 'Express delivery', 'Not available'),
 ('What discount does a Collector member get?', 'Collector', 'Discount', '10 percent'),
 ('Do Patron members get early access to preorders?', 'Patron', 'Early access', 'All preorders 7 days early'),
 ('Can I return an e-book?', 'E-book', 'Return window', 'Not returnable'),
 ('Do Reader members get free shipping on every order?', 'Reader', 'Free shipping', 'Orders above 499 rupees'),
]

def markdown(title, head, rows):
    lines = [title, '| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    return '\n'.join(lines + ['| ' + ' | '.join(r) + ' |' for r in rows])

def fixed_chunks(text, size=160):
    words, out, cur = text.split(' '), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > size and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    return out + ([cur] if cur else [])

def serialize_rows(title, headers, rows, unit_note=""):
    """One retrieval chunk per row: table title, every header beside its cell, optional unit note."""
    chunks = []
    for row in rows:
        cells = "; ".join(f"{h}: {c}" for h, c in zip(headers, row) if c.strip())
        chunks.append(f"{title}. {cells}." + (f" {unit_note}" if unit_note else ""))
    return chunks


def corpus(strategy):
    docs = list(PROSE)
    for title, head, rows in TABLES:
        if strategy == 'fixed':
            docs += fixed_chunks(markdown(title, head, rows))
        elif strategy == 'row':
            docs += ['| ' + ' | '.join(r) + ' |' for r in rows]
        elif strategy == 'row_with_header':
            docs += serialize_rows(title, head, rows)
    return docs

TOKEN = re.compile(r'[a-z0-9]+')
def toks(s):
    return TOKEN.findall(s.lower())

def bm25(docs, query, k1=1.2, b=0.75):
    td = [toks(d) for d in docs]
    avg = sum(map(len, td)) / len(td)
    df = Counter(t for d in td for t in set(d))
    n = len(td)
    scores = []
    for i, d in enumerate(td):
        tf = Counter(d)
        s = 0.0
        for q in toks(query):
            if q not in tf:
                continue
            idf = math.log(1 + (n - df[q] + 0.5) / (df[q] + 0.5))
            s += idf * tf[q] * (k1 + 1) / (tf[q] + k1 * (1 - b + b * len(d) / avg))
        scores.append((s, i))
    return [i for s, i in sorted(scores, key=lambda x: (-x[0], x[1]))]

def answerable(chunk, row_key, column, cell):
    """Strict: the chunk must state the row, the column header and the cell, so a reader can tell
    that '7 days' is the return window of a signed edition and not some other figure."""
    return row_key in chunk and column in chunk and cell in chunk

def evaluate(strategy):
    docs = corpus(strategy)
    top1 = top3 = found3 = 0
    for q, row_key, column, cell in QUESTIONS:
        ranked = bm25(docs, q)
        top1 += answerable(docs[ranked[0]], row_key, column, cell)
        top3 += any(answerable(docs[i], row_key, column, cell) for i in ranked[:3])
        found3 += any(row_key in docs[i] and cell in docs[i] for i in ranked[:3])
    return {'chunks': len(docs), 'row_and_cell@3': found3, 'answerable@1': top1, 'answerable@3': top3}


if __name__ == '__main__':
    for strategy in ('fixed', 'row', 'row_with_header'):
        docs = corpus(strategy)
        top1 = top3 = found3 = 0
        for q, row_key, column, cell in QUESTIONS:
            ranked = bm25(docs, q)
            top1 += answerable(docs[ranked[0]], row_key, column, cell)
            top3 += any(answerable(docs[i], row_key, column, cell) for i in ranked[:3])
            found3 += any(row_key in docs[i] and cell in docs[i] for i in ranked[:3])
        print('%-16s chunks=%2d  row_and_cell@3=%d/%d  answerable@1=%d/%d  answerable@3=%d/%d' % (
            strategy, len(docs), found3, len(QUESTIONS), top1, len(QUESTIONS), top3, len(QUESTIONS)))
