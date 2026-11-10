"""Pre-upgrade checks for two Istio 1.32.0 changes described in its upgrade notes.

Author: Sandeep Belgavi. Input is EnvoyFilter objects already converted to dicts (for example
`kubectl get envoyfilter -A -o json`) and the istiod environment. It reads files only; it never
contacts a cluster. It does not replace `istioctl analyze` or a staging upgrade.
"""
import re

RBAC = 'envoy.filters.http.rbac'
ALLOW = 'istio.authorization.allow'


def _duration_seconds(value):
    if value in (None, ''):
        return None
    if str(value) == '0':
        return 0
    m = re.fullmatch(r'(\d+)(ms|s|m|h)', str(value))
    if not m:
        raise ValueError(f'unparseable duration {value!r}')
    n, unit = int(m[1]), m[2]
    return n / 1000 if unit == 'ms' else n * {'s': 1, 'm': 60, 'h': 3600}[unit]


def envoyfilter_findings(filters, httproute_auth_enabled):
    """Flag gateway patches that address the RBAC filter by name."""
    findings = []
    for f in filters:
        name = f"{f.get('metadata', {}).get('namespace', '?')}/{f.get('metadata', {}).get('name', '?')}"
        for i, patch in enumerate(f.get('spec', {}).get('configPatches', [])):
            match = patch.get('match', {})
            sub = match.get('listener', {}).get('filterChain', {}).get('filter', {}).get('subFilter', {})
            if match.get('context') != 'GATEWAY' or sub.get('name') != RBAC:
                continue
            op = patch.get('patch', {}).get('operation', '')
            if not httproute_auth_enabled:
                findings.append((name, i, op, 'info', 'matches today; re-check before enabling ENABLE_GATEWAY_API_HTTPROUTE_AUTH'))
            elif op in ('INSERT_BEFORE', 'INSERT_AFTER'):
                findings.append((name, i, op, 'high', f'no longer matches the ALLOW filter ({ALLOW}); the inserted filter is dropped'))
            else:
                findings.append((name, i, op, 'high', f'no longer applies to the ALLOW filter ({ALLOW}); DENY and AUDIT still match'))
    return findings


def timeout_findings(env, apiserver_request_timeout='60s'):
    """Check the new client-side Kubernetes API timeouts against the API server's request timeout."""
    findings = []
    header = _duration_seconds(env.get('ISTIO_KUBE_HEADER_TIMEOUT', '90s'))
    request = _duration_seconds(env.get('ISTIO_KUBE_REQUEST_TIMEOUT', '15m'))
    server = _duration_seconds(apiserver_request_timeout)
    if header == 0:
        findings.append(('ISTIO_KUBE_HEADER_TIMEOUT', 'info', 'set to 0: unbounded, the pre-1.32 behaviour'))
    elif header <= server:
        findings.append(('ISTIO_KUBE_HEADER_TIMEOUT', 'high', f'{header:g}s must stay above the API server --request-timeout ({server:g}s)'))
    if request == 0:
        findings.append(('ISTIO_KUBE_REQUEST_TIMEOUT', 'info', 'set to 0: unbounded, the pre-1.32 behaviour'))
    elif request < header:
        findings.append(('ISTIO_KUBE_REQUEST_TIMEOUT', 'warn', 'total request timeout is shorter than the header timeout'))
    return findings


def sample_filter(op):
    return {'metadata': {'namespace': 'istio-system', 'name': 'books-gateway-rbac'},
            'spec': {'configPatches': [{'applyTo': 'HTTP_FILTER',
                                        'match': {'context': 'GATEWAY', 'listener': {'filterChain': {'filter': {
                                            'name': 'envoy.filters.network.http_connection_manager',
                                            'subFilter': {'name': RBAC}}}}},
                                        'patch': {'operation': op}}]}}
