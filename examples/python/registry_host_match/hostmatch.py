# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

"""Deciding whether a registry host may receive an Azure credential: unanchored versus exact matching.

Illustrates the kaniko helper mistake (GHSA-5q7h-w9jf-cx97). This is not kaniko code.
"""
import re

UNSAFE = re.compile(r"\.azurecr\.(io|cn|de|us)")
ACR_SUFFIXES = (".azurecr.io", ".azurecr.cn", ".azurecr.de", ".azurecr.us")
HOST_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*(:\d{1,5})?$")


def unsafe_is_acr(registry):
    return UNSAFE.search(registry) is not None


def is_acr_host(registry):
    host = registry.strip().lower()
    if not HOST_RE.fullmatch(host):
        return False
    name = host.split(":", 1)[0]
    if name == "mcr.microsoft.com":
        return True
    return any(name.endswith(s) and len(name) > len(s) for s in ACR_SUFFIXES)


if __name__ == "__main__":
    for h in ("store.azurecr.io", "store.azurecr.io.attacker.example"):
        print(h, "unsafe:", unsafe_is_acr(h), "safe:", is_acr_host(h))
