"""Count tokens for the same synthetic Belgavi's Book Store texts under five public tokenizers.

Author: Sandeep Belgavi. Companion to "Same Text, Different Token Counts" (aicassindra.com).
Raw tokenizer counts only: no chat template, no special tokens, no provider message overhead.
Run fetch_tokenizers.py once (network) before this script; counting itself is offline after tiktoken
has cached its two encodings.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TOKDIR = os.path.join(HERE, 'tokenizer_files')

HELPDESK = ("Hello, this is Jenya. I ordered three paperbacks on 14 October (order BK-58213) and only two arrived. "
            "The missing one is The Left Hand of Darkness. The parcel looked opened and resealed. Could you either "
            "send the missing book or refund it to my store credit? I would also like to know whether the 10 percent "
            "member discount was applied, because the invoice shows the full price for all three books. Thanks, Jenya")
ORDER = {"order_id": "BK-58213", "customer": "Jenya", "placed_at": "2026-10-14T09:32:11+05:30",
         "lines": [{"sku": "PB-0441", "title": "The Left Hand of Darkness", "qty": 1, "unit_price": 399.0},
                   {"sku": "PB-1902", "title": "Kindred", "qty": 1, "unit_price": 349.0},
                   {"sku": "PB-2210", "title": "The Dispossessed", "qty": 1, "unit_price": 425.0}],
         "discount_pct": 0, "member": True, "shipment": {"carrier_ref": "SHP-77120394", "status": "delivered_partial"}}
CODE = '''def refund_amount(order, missing_skus, member_discount=0.10):
    """Refund the missing lines at the price actually charged."""
    total = 0.0
    for line in order["lines"]:
        if line["sku"] in missing_skus:
            price = line["unit_price"] * line["qty"]
            if order.get("member") and order.get("discount_pct", 0) == 0:
                price *= (1 - member_discount)
            total += price
    return round(total, 2)
'''
HINDI = "नमस्ते, मेरा ऑर्डर अभी तक पूरा नहीं आया है। तीन किताबों में से केवल दो पहुँचीं। कृपया बताइए कि बाकी किताब कब भेजी जाएगी या उसका पैसा वापस कब मिलेगा।"
KANNADA = "ನಮಸ್ಕಾರ, ನನ್ನ ಆರ್ಡರ್ ಇನ್ನೂ ಪೂರ್ತಿಯಾಗಿ ಬಂದಿಲ್ಲ. ಮೂರು ಪುಸ್ತಕಗಳಲ್ಲಿ ಎರಡು ಮಾತ್ರ ತಲುಪಿವೆ. ಉಳಿದ ಪುಸ್ತಕವನ್ನು ಯಾವಾಗ ಕಳುಹಿಸುತ್ತೀರಿ ಎಂದು ದಯವಿಟ್ಟು ತಿಳಿಸಿ."
LOGS = "\n".join("2026-10-14T09:%02d:%02d.%03dZ INFO req=%08x-4c1e-4b7a-9f2d-%012x path=/orders/BK-%05d status=%d ms=%d"
                 % (30 + i, (i * 17) % 60, (i * 131) % 1000, 0x5e1d0000 + i * 7919, 0x1a2b3c4d5e6f + i * 104729,
                    58200 + i, (200, 200, 404, 200, 500)[i % 5], 12 + (i * 37) % 300) for i in range(8))

SAMPLES = [
    ('English help-desk message', HELPDESK),
    ('Order record, compact JSON', json.dumps(ORDER, separators=(',', ':'))),
    ('Order record, indented JSON', json.dumps(ORDER, indent=2)),
    ('Python function', CODE),
    ('Hindi message', HINDI),
    ('Hindi message inside JSON, ensure_ascii=True', json.dumps({"message": HINDI})),
    ('Hindi message inside JSON, ensure_ascii=False', json.dumps({"message": HINDI}, ensure_ascii=False)),
    ('Kannada message', KANNADA),
    ('Eight log lines with ids and timestamps', LOGS),
]

HF_FILES = (('Qwen2.5', 'Qwen_Qwen2.5-0.5B-Instruct.json'), ('Phi-3.5-mini', 'microsoft_Phi-3.5-mini-instruct.json'),
            ('DeepSeek-V3', 'deepseek-ai_DeepSeek-V3.json'))


def tokenizers():
    import tiktoken
    from tokenizers import Tokenizer
    out = [('cl100k_base', tiktoken.get_encoding('cl100k_base').encode_ordinary),
           ('o200k_base', tiktoken.get_encoding('o200k_base').encode_ordinary)]
    for name, fn in HF_FILES:
        tk = Tokenizer.from_file(os.path.join(TOKDIR, fn))
        out.append((name, lambda s, tk=tk: tk.encode(s, add_special_tokens=False).ids))
    return out


def measure():
    toks = tokenizers()
    rows = []
    for label, text in SAMPLES:
        row = {'sample': label, 'chars': len(text)}
        row.update({name: len(enc(text)) for name, enc in toks})
        rows.append(row)
    return [n for n, _ in toks], rows


def main():
    names, rows = measure()
    print('%-46s %6s ' % ('sample', 'chars') + ' '.join('%12s' % n for n in names))
    for r in rows:
        print('%-46s %6d ' % (r['sample'], r['chars']) + ' '.join('%12d' % r[n] for n in names))
    print('%-46s %6d ' % ('TOTAL', sum(r['chars'] for r in rows)) + ' '.join('%12d' % sum(r[n] for r in rows) for n in names))


if __name__ == '__main__':
    main()
