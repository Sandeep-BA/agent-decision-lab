"""An SQS batch handler for AWS Lambda that reports only the failed messages.

Author: Sandeep Belgavi.

Turn on ReportBatchItemFailures on the event source mapping, then return
{"batchItemFailures": [{"itemIdentifier": <messageId>}, ...]}. Lambda deletes the other messages
and makes only the listed ones visible again after the visibility timeout. Raising an exception
fails the whole batch, so the handler catches per-record errors. For a FIFO queue it stops at the
first failure and reports that record and every later one, so a message group keeps its order.
"""
from __future__ import annotations

import json


class Poison(Exception):
    """A record that can never succeed: report it as failed and let maxReceiveCount move it to the DLQ."""


def process_return_request(body: dict, store: dict) -> None:
    """Idempotent effect: record a return for an order once, keyed by the request id."""
    if 'order_id' not in body or 'request_id' not in body:
        raise Poison('missing order_id or request_id')
    if body.get('simulate') == 'downstream_timeout':
        raise TimeoutError('returns service timed out')
    store.setdefault(body['request_id'], {'order_id': body['order_id'], 'applied': 0})
    store[body['request_id']]['applied'] = 1     # a redelivery of a processed record changes nothing


def handle(event: dict, store: dict, fifo: bool = False) -> dict:
    failures = []
    records = event.get('Records', [])
    for index, record in enumerate(records):
        try:
            process_return_request(json.loads(record['body']), store)
        except Exception:                      # one record's failure must not fail the batch
            if fifo:
                failures.extend({'itemIdentifier': r['messageId']} for r in records[index:])
                break
            failures.append({'itemIdentifier': record['messageId']})
    return {'batchItemFailures': failures}


def lambda_handler(event, context):            # entry point name used by the Lambda runtime
    return handle(event, STORE, fifo=event.get('Records', [{}])[0].get('eventSourceARN', '').endswith('.fifo'))


STORE: dict = {}                               # stand-in for a table with a conditional put
