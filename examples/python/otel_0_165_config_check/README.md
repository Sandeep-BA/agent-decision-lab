# OpenTelemetry Collector 0.165.0 config review

**Author: Sandeep Belgavi**

A runnable companion to *OpenTelemetry Collector 0.165: Removed HTTP Client Fields and the Double-Batching Warning* (aicassindra.com). Flags deprecated HTTP client keep-alive keys that belong under `keepalive`, pipelines that use the batch processor together with exporter batching, and the removed SignalFx receiver.

## Prerequisites

- Python 3.11 or newer. Standard library only; nothing to install (`requirements.txt` is intentionally empty).
- No network, no credentials and no model call. `.env.example` documents that nothing is read from the environment.

## Sample input

`SAMPLE` in `config_check.py`: one OTLP/HTTP exporter with legacy keep-alive keys and sending-queue batching behind a batch processor.

## Commands

```
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Four tests pass; the sample yields exactly three findings and the corrected configuration yields none.

## Limitations

Works on an already-parsed dict and covers only the three checks above. Run `otelcol validate --config=...` with the 0.165.0 binary before rollout.

Views are my own and do not represent any employer, past or present.
