"""What a retried Elasticsearch _bulk request stores. Author: Sandeep Belgavi.

A model of the retry settings documented for the OpenTelemetry Collector Contrib Elasticsearch exporter:
v0.165.0 defaulted retry_on_status and retry_on_document_status to [429]; v0.166.0 (2026-11-24) retries the
whole bulk request on transport errors, client timeouts and statuses 400, 401, 403, 404, 409, 429, 500, 502,
503 and 504, and failed documents on 429, 500, 502, 503 and 504. The exporter sends every document with the
create action (exporter.go at v0.166.0), so a document that carries an explicit _id is rejected with 409 when
it already exists. The store below is a dictionary, not Elasticsearch; no cluster is contacted.
"""
import itertools, json, sys

V165 = {'retry_on_status': {429}, 'retry_on_document_status': {429}, 'retry_on_timeout': False, 'max_retries': 2}
V166 = {'retry_on_status': {400, 401, 403, 404, 409, 429, 500, 502, 503, 504},
        'retry_on_document_status': {429, 500, 502, 503, 504}, 'retry_on_timeout': True, 'max_retries': 2}


class Store:
    def __init__(self):
        self.docs, self.auto = {}, itertools.count(1)

    def create(self, doc):
        if doc.get('_id') is None:
            self.docs[f'auto-{next(self.auto)}'] = doc['body']; return 201
        if doc['_id'] in self.docs:
            return 409
        self.docs[doc['_id']] = doc['body']; return 201


def export(batch, settings, faults):
    """faults: list per attempt, one of 'ok', 'lost-response', 'http-503-before-apply', 'http-400', or
    ('doc-429', set_of_positions). Returns stored documents and what the exporter reports."""
    store, trace = Store(), []
    pending, failed, attempts = list(batch), [], 0
    while pending:
        fault = faults[attempts] if attempts < len(faults) else 'ok'
        attempts += 1
        kind = fault[0] if isinstance(fault, tuple) else fault
        if kind in ('http-503-before-apply', 'http-400'):
            status = 503 if kind == 'http-503-before-apply' else 400
            trace.append(f'attempt {attempts}: HTTP {status}, nothing applied')
            if status in settings['retry_on_status'] and attempts <= settings['max_retries']:
                continue
            failed += [(d['body']['n'], status) for d in pending]; break
        statuses = []
        for pos, d in enumerate(pending):
            if kind == 'doc-429' and pos in fault[1]:
                statuses.append(429)
            else:
                statuses.append(store.create(d))
        if kind == 'lost-response':
            trace.append(f'attempt {attempts}: applied {statuses.count(201)} documents, response lost (client timeout)')
            if settings['retry_on_timeout'] and attempts <= settings['max_retries']:
                continue
            failed += [(d['body']['n'], 'timeout') for d in pending]; break
        trace.append(f'attempt {attempts}: item statuses {statuses}')
        retry = [d for d, s in zip(pending, statuses) if s in settings['retry_on_document_status']]
        failed += [(d['body']['n'], s) for d, s in zip(pending, statuses) if s not in (201,) and s not in settings['retry_on_document_status']]
        if retry and attempts <= settings['max_retries']:
            pending = retry; continue
        failed += [(d['body']['n'], s) for d, s in zip(pending, statuses) if s in settings['retry_on_document_status']]
        break
    stored = list(store.docs.values())
    unique = {d['n'] for d in stored}
    return {'attempts': attempts, 'stored_documents': len(stored), 'distinct_records_stored': len(unique),
            'duplicates': len(stored) - len(unique), 'lost_records': len(batch) - len(unique),
            'reported_failed': sorted(failed, key=str), 'trace': trace}


def batch(n=5, with_ids=False):
    return [{'_id': f'log-CASE-61{i:02d}-{i}' if with_ids else None, 'body': {'n': i, 'case': f'CASE-61{i:02d}'}} for i in range(n)]


SCENARIOS = {
    'lost response, no ids': (False, ['lost-response']),
    'lost response, deterministic ids': (True, ['lost-response']),
    '503 before apply': (False, ['http-503-before-apply']),
    'two documents rejected with 429': (False, [('doc-429', {1, 3})]),
    'malformed request (400)': (False, ['http-400', 'http-400', 'http-400']),
}


def main():
    out = {}
    for name, (ids, faults) in SCENARIOS.items():
        out[name] = {'v0.165.0 defaults': export(batch(with_ids=ids), V165, faults),
                     'v0.166.0 defaults': export(batch(with_ids=ids), V166, faults)}
    json.dump(out, sys.stdout, indent=2, default=list); print()
    return json.loads(json.dumps(out, default=list))


if __name__ == '__main__':
    main()
