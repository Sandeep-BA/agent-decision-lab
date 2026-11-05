# sqs_partial_batch

**Author: Sandeep Belgavi**

Companion to the guide *Stop One Bad SQS Message From Redelivering the Whole Lambda Batch* on
aicassindra.com.

- `handler.py`: a Lambda handler for SQS that catches errors per record and returns
  `{"batchItemFailures": [{"itemIdentifier": ...}]}`. On a FIFO queue it reports the first failure and
  every later record, as the AWS Lambda documentation asks. The effect is idempotent per `request_id`.
- `queue_sim.py`: a deterministic stand-in for the queue and event source mapping: batches, receive
  counts, redrive to a dead-letter queue after `max_receive_count`, and Lambda's rule that a whole
  batch returns to the queue when the function fails or reports an `itemIdentifier` that is not in the batch.
- `fixtures.json`: ten synthetic return requests. `m07` lacks an `order_id` (a poison message);
  `m03` times out once.

## Prerequisites

Python 3.11 or newer, standard library only. Tested with Python 3.13.5. Nothing here calls AWS.

## Run

```
python demo.py
python -m unittest -v
```

Expected output (`expected_output.txt`):

```
raise           invocations=5 deliveries=50 redeliveries=40 dead_lettered=m01,m02,m03,m04,m05,m06,m07,m08,m09,m10 applied=9
partial         invocations=5 deliveries=15 redeliveries=5 dead_lettered=m07 applied=9
partial_bad_id  invocations=5 deliveries=50 redeliveries=40 dead_lettered=m01,m02,m03,m04,m05,m06,m07,m08,m09,m10 applied=9
```

`raise`: the function fails the batch on any error, so the poison message drags the nine good ones
through five receives and into the dead-letter queue. `applied=9` holds only because the effect is
idempotent. `partial`: only `m03` (once) and `m07` (until redrive) come back.

## Deploying the handler

Enable partial batch responses on the event source mapping:

```
aws lambda update-event-source-mapping --uuid <mapping-uuid> --function-response-types "ReportBatchItemFailures"
```

## Limitations

- The simulator has no clock, polling concurrency, batching window or throttling. It counts receives,
  not seconds. Real redelivery waits for the visibility timeout.
- `STORE` in `handler.py` is an in-memory stand-in. In Lambda, use a table with a conditional write keyed
  by `request_id`; module state does not survive across execution environments.
- Not tested against a real queue in this repository.
