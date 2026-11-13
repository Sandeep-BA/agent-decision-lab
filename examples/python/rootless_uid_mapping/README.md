# Rootless Podman UID mapping arithmetic

**Author: Sandeep Belgavi**

A runnable companion to *Rootless Podman Bind Mounts: Why Files Show Up as 100999 and What --userns=keep-id Changes* (aicassindra.com). An original calculator for where a container UID lands on the host under rootless Podman, by default and with --userns=keep-id, following the podman-run documentation and the mapping visible in Podman v6.2.0 source. It parses /etc/subuid text and inverts mappings to show how a host-owned file appears in the container.

## Prerequisites

- Python 3.11 or newer. Standard library only. Podman is not needed and was not run.
- `.env.example` documents that nothing secret is read from the environment. No API keys, no network calls beyond loopback.

## Sample input

Synthetic /etc/subuid lines jenya:100000:65536 and geetha:165536:65536, host UID 1000.

## Commands

From this directory:

```
python uid_mapping.py
python -m unittest discover -s . -p "test_*.py" -v
```

## Expected output

Default: container 0 -> host 1000, container 1000 -> host 100999, and your host file appears as root (0). keep-id: segments (0,1,1000), (1000,0,1), (1001,1001,64536); container 1000 -> host 1000 and container 0 -> host 100000. 9 tests pass.

## Limitations

Arithmetic only. GID maps follow the same rules but are not modelled separately; --userns=auto, idmapped mounts and the :U volume option are not modelled. Check real mappings with podman unshare cat /proc/self/uid_map.

Views are my own and do not represent any employer, past or present.
