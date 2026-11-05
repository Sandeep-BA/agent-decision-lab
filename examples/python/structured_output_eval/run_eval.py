"""Run the twelve cases against a local Ollama model in three output modes, or re-score recorded runs.

Author: Sandeep Belgavi.
  python run_eval.py --live --model qwen2.5:0.5b-instruct   # calls Ollama, writes recordings/<model>.json
  python run_eval.py                                         # offline: scores recordings/*.json only
Modes: prompt (JSON requested in the prompt only), json (format="json"), schema (format=<JSON schema>).
"""
import argparse
import json
import os
import pathlib
import urllib.request

from schema import FIELDS, SCHEMA, problems

HERE = pathlib.Path(__file__).resolve().parent
MODES = ('prompt', 'json', 'schema')
OPTIONS = {'temperature': 0, 'seed': 7}
PROMPT = ('Extract fields from a bookshop help-desk message. Reply with only a JSON object that matches this '
          'JSON schema, using null when a value is not stated:\n%s\n\nMessage: %s')


def call(model, text, mode, host):
    body = {'model': model, 'stream': False, 'options': OPTIONS,
            'messages': [{'role': 'user', 'content': PROMPT % (json.dumps(SCHEMA), text)}]}
    if mode == 'json':
        body['format'] = 'json'
    elif mode == 'schema':
        body['format'] = SCHEMA
    req = urllib.request.Request(host + '/api/chat', data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=300))['message']['content']


def score(cases, outputs):
    totals = dict(parsed=0, valid=0, all_correct=0, **{f: 0 for f in FIELDS})
    for case in cases:
        try:
            obj = json.loads(outputs[case['id']])
        except ValueError:
            continue
        totals['parsed'] += 1
        if not problems(obj):
            totals['valid'] += 1
        hits = [isinstance(obj, dict) and obj.get(f) == case['gold'][f] for f in FIELDS]
        for f, ok in zip(FIELDS, hits):
            totals[f] += ok
        totals['all_correct'] += all(hits)
    return totals


def record(model, host, cases):
    version = json.load(urllib.request.urlopen(host + '/api/version', timeout=10))['version']
    outputs = {m: {c['id']: call(model, c['text'], m, host) for c in cases} for m in MODES}
    return {'model': model, 'ollama': version, 'options': OPTIONS, 'outputs': outputs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--model', default='qwen2.5:0.5b-instruct')
    ap.add_argument('--host', default=os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434'))
    args = ap.parse_args()
    cases = json.loads((HERE / 'cases.json').read_text(encoding='utf-8'))['cases']
    rec_dir = HERE / 'recordings'
    if args.live:
        rec_dir.mkdir(exist_ok=True)
        rec = record(args.model, args.host, cases)
        path = rec_dir / (args.model.replace(':', '_') + '.json')
        path.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    for path in sorted(rec_dir.glob('*.json')):
        rec = json.loads(path.read_text(encoding='utf-8'))
        for mode in MODES:
            t = score(cases, rec['outputs'][mode])
            detail = ', '.join('%s %d' % (f, t[f]) for f in FIELDS)
            print('%-22s %-6s parsed %2d/12  schema-valid %2d/12  all fields right %2d/12  (%s)' % (
                rec['model'], mode, t['parsed'], t['valid'], t['all_correct'], detail))


if __name__ == '__main__':
    main()
