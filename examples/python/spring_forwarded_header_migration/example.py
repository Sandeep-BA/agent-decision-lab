"""Check Spring Boot 4.2 forwarded-header settings before an upgrade. Author: Sandeep Belgavi.

Rules encoded from Spring Boot v4.2.0 sources (read 2026-11-25): ForwardedHeaderStrategy
binds server.request.header.forwarded.strategy and the deprecated
server.forward-headers-strategy, rejects configurations that set both
(MutuallyExclusiveConfigurationPropertiesException) and maps NATIVE -> WEB_SERVER,
FRAMEWORK -> FRAMEWORK, NONE -> NONE. ForwardedRequestHeaders asserts that use-prefix is
only used with x-forwarded naming. This is a static checker for flat .properties input; it
does not start Spring, and relaxed-binding variants beyond kebab/dot case are not handled.
"""
import json

NEW = "server.request.header.forwarded.strategy"
OLD = "server.forward-headers-strategy"
NAMING = "server.request.header.forwarded.naming"
PREFIX = "server.request.header.forwarded.use-prefix"
OLD_TO_NEW = {"native": "web-server", "framework": "framework", "none": "none"}


def parse_properties(text):
    props = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line[0] in "#!":
            continue
        key, _, value = line.partition("=")
        props[key.strip().lower()] = value.strip().lower()
    return props


def check(props, on_cloud_platform=False):
    findings, effective = [], None
    if NEW in props and OLD in props:
        findings.append({"level": "startup-failure", "detail": f"{OLD} and {NEW} are mutually exclusive"})
    elif NEW in props:
        effective = props[NEW]
    elif OLD in props:
        effective = OLD_TO_NEW.get(props[OLD])
        findings.append({"level": "deprecated", "detail": f"replace {OLD}={props[OLD]} with {NEW}={effective}"})
    else:
        effective = "web-server" if on_cloud_platform else "none"
        findings.append({"level": "implicit", "detail": f"no strategy set; default is {effective} "
                         f"({'detected' if on_cloud_platform else 'no'} cloud platform)"})
    if effective is not None and effective not in OLD_TO_NEW.values():
        findings.append({"level": "startup-failure", "detail": f"unknown strategy {effective}"})
    if props.get(PREFIX) == "true" and props.get(NAMING, "x-forwarded") == "rfc-7239":
        findings.append({"level": "startup-failure", "detail": "use-prefix can only be used with x-forwarded naming"})
    if props.get("server.tomcat.remoteip.internal-proxies", None) == "":
        findings.append({"level": "risk", "detail": "empty internal-proxies trusts every proxy (docs: not for production)"})
    if effective == "none":
        findings.append({"level": "check", "detail": "behind a TLS-terminating proxy, request URLs will use the internal scheme and host"})
    return {"effective_strategy": effective, "findings": findings}


SAMPLES = {
    "legacy_native": "server.forward-headers-strategy=native\n",
    "both_set": "server.forward-headers-strategy=framework\nserver.request.header.forwarded.strategy=web-server\n",
    "rfc_with_prefix": "server.request.header.forwarded.strategy=web-server\n"
                       "server.request.header.forwarded.naming=rfc-7239\nserver.request.header.forwarded.use-prefix=true\n",
    "unset_local": "",
    "migrated": "server.request.header.forwarded.strategy=web-server\nserver.tomcat.remoteip.internal-proxies=10\\\\.0\\\\.\\\\d{1,3}\\\\.\\\\d{1,3}\n",
}


def demo():
    return {name: check(parse_properties(text)) for name, text in SAMPLES.items()}


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
