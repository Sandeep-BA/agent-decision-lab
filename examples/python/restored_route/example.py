# Author: Sandeep Belgavi. Nonsecret restored-route preflight.
from urllib.parse import urlsplit

def endpoint_identity(url):
    if not isinstance(url, str) or url != url.strip():
        raise ValueError("endpoint must be text")
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        raise ValueError("HTTPS endpoint required")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("endpoint must contain no credentials, query or fragment")
    port = parts.port if parts.port is not None else 443
    if not 1 <= port <= 65535:
        raise ValueError("invalid endpoint port")
    return (parts.hostname.lower(), port, parts.path or "/")

def resume_route(required, current):
    if current is None:
        return "blocked-missing-route"
    if not isinstance(required, dict) or not isinstance(current, dict):
        return "blocked-invalid-contract"
    if set(required) != {"route", "revision", "endpoint"} or set(current) != set(required):
        return "blocked-invalid-contract"
    if required["route"] != current["route"] or required["revision"] != current["revision"]:
        return "blocked-route-revision"
    if endpoint_identity(required["endpoint"]) != endpoint_identity(current["endpoint"]):
        return "blocked-endpoint-change"
    return "ready-for-credential-resolution"

required = {"route": "synthetic-a", "revision": 3,
            "endpoint": "https://gateway.invalid/model/"}
assert resume_route(required, None) == "blocked-missing-route"
assert resume_route(required, dict(required)) == "ready-for-credential-resolution"


def run_demo(fixture):
    return {"decision":resume_route(fixture["required"],fixture["current"])}

if __name__ == "__main__":
    import json
    from pathlib import Path
    fixture = json.loads(Path(__file__).with_name("sample-input.json").read_text(encoding="utf-8"))
    print(json.dumps(run_demo(fixture),sort_keys=True))
