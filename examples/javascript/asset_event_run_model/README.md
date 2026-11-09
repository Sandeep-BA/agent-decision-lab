# Asset-event grouping and paired-gate models

**Author: Sandeep Belgavi**

A runnable companion to *Airflow 3.4 Changes Asset Event Batching: Plan Your Upgrade* (aicassindra.com). The deterministic models behind two interactive labs: one maps synthetic asset events to runs and slots, the other computes paired evaluation counts.

## Prerequisites

- Node.js 22. No packages, network, credentials or model calls.

## Sample input

Inputs are written in `test-models.cjs`, for example six events at tick zero with two slots and a four-tick run.

## Commands

```
node test-models.cjs
```

## Expected output

18 checks pass. Six per-event runs finish at tick 12 with maximum eligible-queue wait 8. In batch mode the same burst is one run that finishes at tick 4, because this model holds duration fixed regardless of batch size.

## Limitations

This is not an Airflow scheduler or a throughput benchmark. It omits executors, the metadata database, partitions, retries and batch-size-dependent duration. Evaluation power is a normal planning approximation. All data are synthetic.

Views are my own and do not represent any employer, past or present.
