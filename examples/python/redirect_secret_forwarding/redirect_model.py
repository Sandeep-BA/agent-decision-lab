"""Author: Sandeep Belgavi. Offline model of what a client re-sends after one redirect.
Rules follow the WHATWG Fetch "HTTP-redirect fetch" steps and requests' SessionRedirectMixin
(should_strip_auth, rebuild_method, body purge). Cookies, proxies and multi-hop chains are out of scope."""
from urllib.parse import urlsplit

DEFAULT_PORTS = {"http": 80, "https": 443}
CLIENTS = ("fetch", "requests", "copy-all", "no-follow")


def _origin(url):
    u = urlsplit(url)
    return (u.scheme, u.hostname, u.port or DEFAULT_PORTS[u.scheme])


def _requests_strips(old, new):
    o, n = urlsplit(old), urlsplit(new)
    if o.hostname != n.hostname:
        return True
    if o.scheme == "http" and o.port in (80, None) and n.scheme == "https" and n.port in (443, None):
        return False
    changed_port, changed_scheme = o.port != n.port, o.scheme != n.scheme
    default = (DEFAULT_PORTS.get(o.scheme), None)
    if not changed_scheme and o.port in default and n.port in default:
        return False
    return changed_port or changed_scheme


def follow(client, status, method, url, location, secrets):
    """secrets: subset of {'authorization', 'api-key-header', 'body'} present on the first request.
    Returns (followed, new_method, delivered_secrets, trace)."""
    if client not in CLIENTS or status not in (301, 302, 303, 307, 308) or method not in ("GET", "POST"):
        raise ValueError("unsupported input")
    if method == "GET" and "body" in secrets:
        raise ValueError("a GET request carries no body in this model")
    trace = [f"First request: {method} {url} with {', '.join(sorted(secrets)) or 'no secrets'}; response {status} Location {location}."]
    if client == "no-follow":
        trace.append("Redirects are disabled: the client returns the 3xx response and sends nothing to the new location.")
        return False, None, set(), trace
    cross = _origin(url) != _origin(location)
    trace.append(f"The new location is {'a different origin' if cross else 'the same origin'} (scheme, host, port).")
    new_method, delivered = method, set(secrets)
    rewrite = (status in (301, 302) and method == "POST") or (status == 303 and method not in ("GET", "HEAD"))
    if client == "requests":
        rewrite = (status in (302, 303) and method != "HEAD") or (status == 301 and method == "POST")
    if client != "copy-all" and rewrite:
        new_method = "GET"
        if "body" in delivered:
            delivered.discard("body")
            trace.append(f"{status} turns POST into GET, so the body is dropped.")
        else:
            trace.append(f"{status} turns the request into GET.")
    elif "body" in delivered:
        trace.append(f"{status} keeps the method and re-sends the body to {location}." if client != "copy-all" else "The hand-written follow loop copies the method and body unchanged.")
    if "authorization" in delivered:
        strip = cross if client == "fetch" else _requests_strips(url, location) if client == "requests" else False
        if strip:
            delivered.discard("authorization")
            trace.append("Authorization is removed because the " + ("origin" if client == "fetch" else "host, port or scheme") + " changed.")
        else:
            trace.append("Authorization is kept" + (" (requests allows http to https on default ports)." if client == "requests" and cross else "."))
    if "api-key-header" in delivered:
        trace.append("The custom API-key header is not on any strip list, so it goes to the new location.")
    trace.append("Delivered to the new location: " + (", ".join(sorted(delivered)) or "no secrets") + ".")
    return True, new_method, delivered, trace


if __name__ == "__main__":
    s = {"authorization", "api-key-header", "body"}
    for c in CLIENTS:
        for st in (302, 307):
            f, m, d, t = follow(c, st, "POST", "https://auth.example.test/token", "https://login.example.net/token", s)
            print(c, st, m, sorted(d))
