"""Count tokens in tool definitions with a local tokenizer. Author: Sandeep Belgavi.

The counts use tiktoken's o200k_base encoding over compact JSON. Providers render tool definitions
into their own internal format and tokenizers differ, so treat these as relative measurements and
check absolute numbers with your provider's token-counting endpoint before budgeting."""
import json
from catalog import tools


def count(obj, enc):
    return len(enc.encode(json.dumps(obj, separators=(',', ':'), ensure_ascii=False)))


def report(enc):
    rows = {}
    for style in ('concise', 'verbose'):
        defs = tools(style)
        per = sorted(((count(t, enc), t['name']) for t in defs), reverse=True)
        rows[style] = {'tools': len(defs), 'total': count(defs, enc), 'largest': per[:3], 'smallest': per[-1]}
    return rows




ALWAYS_LOADED = ('get_order', 'list_orders', 'add_case_note', 'escalate_case')


def always_loaded_tokens(enc, style='verbose'):
    return count([t for t in tools(style) if t['name'] in ALWAYS_LOADED], enc)


def print_subset():
    import tiktoken
    enc = tiktoken.get_encoding('o200k_base')
    print('always-loaded subset (%s): %d tokens' % (', '.join(ALWAYS_LOADED), always_loaded_tokens(enc)))


if __name__ == '__main__':
    import tiktoken
    enc = tiktoken.get_encoding('o200k_base')
    for style, r in report(enc).items():
        print('%-8s %2d tools  %5d tokens  largest %s  smallest %s' % (style, r['tools'], r['total'], r['largest'], r['smallest']))
    print_subset()
