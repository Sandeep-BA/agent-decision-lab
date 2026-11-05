"""A deterministic stand-in for an SQS queue and a Lambda event source mapping. Author: Sandeep Belgavi.

It models only what the guide needs: batches of up to batch_size visible messages, a receive count
per message, redrive to a dead-letter queue after max_receive_count receives, and Lambda's rule for
which messages return to the queue. It does not model polling concurrency, timing or throttling."""
from __future__ import annotations

import json


def run(messages, handler_mode, batch_size=10, max_receive_count=5, transient_failures=None, max_rounds=20):
    """handler_mode: 'raise' (whole batch fails on any error), 'partial' (batchItemFailures),
    'partial_bad_id' (reports an id that is not in the batch, which Lambda treats as a full failure)."""
    from handler import handle
    transient_failures = dict(transient_failures or {})     # message id -> attempts that time out
    queue = [dict(m, receives=0) for m in messages]
    dlq, store, invocations, deliveries = [], {}, 0, 0
    for _ in range(max_rounds):
        visible = [m for m in queue if not m.get('done')]
        if not visible:
            break
        for start in range(0, len(visible), batch_size):
            batch = visible[start:start + batch_size]
            for m in batch:
                m['receives'] += 1
                deliveries += 1
            invocations += 1
            event = {'Records': [{'messageId': m['id'], 'body': json.dumps(_body(m, transient_failures))} for m in batch]}
            if handler_mode == 'raise':
                result = handle(event, store)
                failed = {m['id'] for m in batch} if result['batchItemFailures'] else set()
            else:
                result = handle(event, store)
                ids = {f['itemIdentifier'] for f in result['batchItemFailures']}
                if handler_mode == 'partial_bad_id' and ids:
                    ids = ids | {'not-in-this-batch'}
                failed = {m['id'] for m in batch} if ids - {m['id'] for m in batch} else ids
            for m in batch:
                if m['id'] not in failed:
                    m['done'] = True
                elif m['receives'] >= max_receive_count:
                    m['done'] = True
                    dlq.append(m['id'])
    return {'invocations': invocations, 'deliveries': deliveries, 'redeliveries': deliveries - len(messages),
            'dead_lettered': sorted(dlq), 'applied': sum(v['applied'] for v in store.values())}


def _body(m, transient):
    body = dict(m['body'])
    if transient.get(m['id'], 0) > 0:
        transient[m['id']] -= 1
        body['simulate'] = 'downstream_timeout'
    return body
