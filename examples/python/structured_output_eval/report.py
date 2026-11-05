"""Offline report over the recordings: schema validity, field accuracy and what grounding catches.
Author: Sandeep Belgavi. Run: python report.py"""
import json, pathlib
from grounding import ungrounded
from run_eval import MODES, score
from schema import problems

HERE = pathlib.Path(__file__).resolve().parent
CASES = json.loads((HERE / 'cases.json').read_text(encoding='utf-8'))['cases']


def wrong_ids(rec, mode):
    """(case id, value) for order ids that are wrong, split by whether the schema validator or grounding sees them."""
    out = {'schema_catches': [], 'grounding_catches': [], 'nobody_catches': []}
    for c in CASES:
        try:
            obj = json.loads(rec['outputs'][mode][c['id']])
        except ValueError:
            continue
        if obj.get('order_id') == c['gold']['order_id']:
            continue
        if 'order_id pattern' in problems(obj):
            out['schema_catches'].append((c['id'], obj.get('order_id')))
        elif 'order_id' in ungrounded(obj, c['text']):
            out['grounding_catches'].append((c['id'], obj.get('order_id')))
        else:
            out['nobody_catches'].append((c['id'], obj.get('order_id')))
    return out


def main():
    for path in sorted((HERE / 'recordings').glob('*.json')):
        rec = json.loads(path.read_text(encoding='utf-8'))
        for mode in MODES:
            t = score(CASES, rec['outputs'][mode])
            w = wrong_ids(rec, mode)
            print('%-22s %-6s valid %2d/12  all right %2d/12  wrong order ids: schema catches %s, grounding catches %s, missed %s' % (
                rec['model'], mode, t['valid'], t['all_correct'], w['schema_catches'] or '-', w['grounding_catches'] or '-', w['nobody_catches'] or '-'))


if __name__ == '__main__':
    main()
