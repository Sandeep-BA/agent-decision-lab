"""Policies for falling back from a WebSocket transport to HTTP for model requests.

Author: Sandeep Belgavi. Original model of the trade-offs discussed in two
openai/codex pull requests that both shipped in rust-v0.168.0: #58950 (probe
WebSocket in the background during HTTP fallback, replay a request whose
recovered connection fails before output) and #58989, merged later the same
day, which keeps HTTP for the rest of the session and removes the probes. No
Codex code is used and no model is called.

A session is a list of requests. The network is a script: for each request
index, what the WebSocket does ("ok", "fail_before_output", "fail_after_output",
"426"). HTTP always succeeds. A failure after output is
counted separately because a replay can repeat output the user already saw;
the policies below never retry such a request on WebSocket.
"""
from dataclasses import dataclass, field

POLICIES = ("per_request", "sticky", "probe_recover")


@dataclass
class Stats:
    ws_attempts: int = 0
    http_requests: int = 0
    probes: int = 0
    retries_used: int = 0
    duplicate_output_risk: int = 0
    transport: list = field(default_factory=list)
    log: list = field(default_factory=list)


def run(policy, ws_script, ws_retries=2, probe_every=1):
    if policy not in POLICIES:
        raise ValueError(policy)
    s = Stats()
    on_http = False
    pinned = False      # 426 or exhausted recovery: never try WebSocket again
    for i, ws in enumerate(ws_script):
        if on_http and policy == "probe_recover" and not pinned and i % probe_every == 0:
            s.probes += 1
            if ws == "ok":
                on_http = False
                s.log.append(f"req {i}: background probe succeeded; next request uses WebSocket")
            elif ws == "426":
                pinned = True
        if on_http:
            s.http_requests += 1
            s.transport.append("http")
            continue
        tries = 0
        while True:
            s.ws_attempts += 1
            if ws == "ok":
                s.transport.append("ws")
                break
            if ws == "426":
                s.log.append(f"req {i}: 426 Upgrade Required; stay on HTTP")
                pinned = True
                on_http = True
                s.http_requests += 1
                s.transport.append("http")
                break
            if ws == "fail_after_output":
                # Output already reached the user: a replay can repeat it.
                s.duplicate_output_risk += 1
                s.retries_used += 1
            else:
                s.retries_used += 1
            tries += 1
            if tries > ws_retries or ws == "fail_after_output":
                s.log.append(f"req {i}: WebSocket gave up after {tries} attempt(s); HTTP")
                s.http_requests += 1
                s.transport.append("http")
                on_http = policy in ("sticky", "probe_recover")
                break
    return s


def summary(policy, script, **kw):
    s = run(policy, script, **kw)
    return {"policy": policy, "ws_attempts": s.ws_attempts, "http": s.http_requests, "probes": s.probes,
            "retries": s.retries_used, "transport": "".join("W" if t == "ws" else "H" for t in s.transport)}


# A transient outage: requests 2-3 fail on WebSocket, the network recovers at 4.
TRANSIENT = ["ok", "ok", "fail_before_output", "fail_before_output", "ok", "ok", "ok", "ok"]
# A proxy that never upgrades.
PROXY_426 = ["426"] * 8
# A link that fails WebSocket every other request.
FLAPPING = ["ok", "fail_before_output"] * 4

if __name__ == "__main__":
    for name, script in (("transient", TRANSIENT), ("proxy 426", PROXY_426), ("flapping", FLAPPING)):
        for p in POLICIES:
            print(f"{name:10}", summary(p, script))
