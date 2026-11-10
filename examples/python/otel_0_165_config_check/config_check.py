"""Pre-upgrade review of an OpenTelemetry Collector config for 0.165.0 changes.

Author: Sandeep Belgavi. Input is the collector config already loaded as a dict (YAML parsed by your
own tooling). It flags (1) HTTP client keep-alive keys deprecated in favour of the `keepalive`
section, (2) pipelines that batch twice: the batch processor plus exporter batching, and (3) the
removed SignalFx receiver. It does not run a collector; confirm with `otelcol validate`.
"""
LEGACY_CLIENT_KEYS = ('idle_conn_timeout', 'max_idle_conns', 'max_idle_conns_per_host', 'disable_keep_alives')


def _component(kind_name):
    return kind_name.split('/', 1)[0]


def _exporter_batches(cfg):
    queue = cfg.get('sending_queue') or {}
    batch = queue.get('batch')
    return queue.get('enabled', True) is not False and isinstance(batch, dict) and batch.get('enabled', True) is not False


def review(config):
    findings = []
    for name, cfg in (config.get('exporters') or {}).items():
        cfg = cfg or {}
        for key in LEGACY_CLIENT_KEYS:
            if key in cfg:
                target = 'keepalive.enabled: false' if key == 'disable_keep_alives' else f'keepalive.{key}'
                findings.append(('warn', f'exporters.{name}.{key}', f'move to {target}'))
    for name in (config.get('receivers') or {}):
        if _component(name) == 'signalfx':
            findings.append(('high', f'receivers.{name}', 'SignalFx receiver removed from contrib in 0.165.0; use OTLP'))
    exporters = config.get('exporters') or {}
    for pname, pipe in ((config.get('service') or {}).get('pipelines') or {}).items():
        if not any(_component(p) == 'batch' for p in pipe.get('processors', [])):
            continue
        for ex in pipe.get('exporters', []):
            if _exporter_batches(exporters.get(ex) or {}):
                findings.append(('warn', f'service.pipelines.{pname}', f'batch processor and {ex} sending_queue batching both enabled'))
    return findings


SAMPLE = {
    'receivers': {'otlp': {'protocols': {'grpc': {}}}},
    'processors': {'batch': {}, 'memory_limiter': {'check_interval': '1s', 'limit_percentage': 80}},
    'exporters': {
        'otlp_http/books': {'endpoint': 'https://collector.books.example', 'max_idle_conns': 50, 'idle_conn_timeout': '60s',
                            'sending_queue': {'batch': {'flush_timeout': '200ms'}}},
    },
    'service': {'pipelines': {'traces': {'receivers': ['otlp'], 'processors': ['memory_limiter', 'batch'], 'exporters': ['otlp_http/books']}}},
}
