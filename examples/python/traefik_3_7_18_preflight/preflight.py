"""Offline preflight for the three Traefik v3.7.18 migration notes. Author: Sandeep Belgavi.

1. Dot-segments with path parameters: model of sanitizePath before and after v3.7.18, applied to
   your own router prefixes, plus a model of a backend that strips path parameters.
2. BasicAuth: passwords longer than 1024 bytes are now rejected with 401.
3. Ingress-NGINX provider: settings on the `default` TLS option no longer apply to Ingress hosts.

This is a model written from the migration guide and the request-path documentation, not
Traefik's code. It never contacts a cluster or a proxy. Confirm with a staging Traefik.
"""


def _clean(segments, keep_trailing):
    out = []
    for s in segments:
        if s in ('', '.'):
            continue
        if s == '..':
            if out:
                out.pop()
            continue
        out.append(s)
    path = '/' + '/'.join(out)
    if keep_trailing and path != '/':
        path += '/'
    return path


def sanitize(path, v3718=True):
    """sanitizePath model. From v3.7.18, a '.', '..' or empty segment that carries ;parameters is
    first reduced to the bare segment, so it is resolved like a plain dot-segment."""
    segments = path.split('/')
    if v3718:
        segments = [s.split(';', 1)[0] if s.split(';', 1)[0] in ('', '.', '..') else s for s in segments]
    return _clean(segments, keep_trailing=path.endswith('/'))


def backend_view(path):
    """A backend that removes ;parameters from every segment and then resolves dot-segments,
    as the Traefik pull request describes for Servlet containers and Spring."""
    segments = [s.split(';', 1)[0] for s in path.split('/')]
    return _clean(segments, keep_trailing=path.endswith('/'))


def route(path, routers):
    """Longest matching PathPrefix wins. routers: list of (name, prefix, middlewares)."""
    best = None
    for name, prefix, middlewares in routers:
        if path == prefix or path.startswith(prefix.rstrip('/') + '/'):
            if best is None or len(prefix) > len(best[1]):
                best = (name, prefix, middlewares)
    return best


def split_views(paths, routers):
    """Report where each request is routed and what the backend finally resolves it to."""
    rows = []
    for p in paths:
        for label, v in (('before', False), ('v3.7.18', True)):
            forwarded = sanitize(p, v)
            r = route(forwarded, routers)
            backend = backend_view(forwarded)
            owner = route(backend, routers)
            rows.append({'request': p, 'traefik': label, 'forwarded': forwarded,
                         'router': r[0] if r else None, 'middlewares': r[2] if r else (),
                         'backend_resolves': backend, 'backend_owner': owner[0] if owner else None,
                         'split_view': bool(r and owner and r[0] != owner[0])})
    return rows


def basicauth_too_long(passwords):
    """Names of users whose password exceeds 1024 bytes in UTF-8 (now rejected with 401)."""
    return sorted(u for u, pw in passwords.items() if len(pw.encode('utf-8')) > 1024)


def default_tls_settings_lost(config):
    """With the Ingress-NGINX provider enabled, list default TLS option settings that no longer
    apply to Ingress hosts, because each host now gets its own generated TLS option."""
    if 'kubernetesIngressNGINX' not in config.get('providers', {}):
        return []
    default = config.get('tls', {}).get('options', {}).get('default', {})
    return sorted(k for k in default if k in ('minVersion', 'maxVersion', 'cipherSuites', 'curvePreferences', 'sniStrict'))


ROUTERS = [('help-public', '/help', ()), ('help-admin', '/help/admin', ('staff-auth',))]
REQUESTS = ['/help/..;/help/admin/cases', '/help/admin/cases', '/help/.;x/admin/cases', '/help/articles/;v=2/returns']

if __name__ == '__main__':
    for row in split_views(REQUESTS, ROUTERS):
        print(row)
    print('basicauth', basicauth_too_long({'geetha': 'short', 'svc-export': 'x' * 1500}))
    print('tls', default_tls_settings_lost({'providers': {'kubernetesIngressNGINX': {}}, 'tls': {'options': {'default': {'minVersion': 'VersionTLS12', 'cipherSuites': ['TLS_AES_128_GCM_SHA256']}}}}))
