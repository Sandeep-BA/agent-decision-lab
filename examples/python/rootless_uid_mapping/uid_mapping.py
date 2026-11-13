"""Where a container UID lands on the host under rootless Podman.

Author: Sandeep Belgavi. Original implementation of the mapping rules described
in the podman-run --userns documentation and visible in Podman v6.2.0's
pkg/util getRootlessKeepIDMapping. Pure arithmetic; it does not run Podman.

Rootless Podman works through two layers:
  intermediate namespace (the user's own): 0 -> $UID, 1..N -> the /etc/subuid range
  container namespace: maps container IDs onto intermediate IDs
"""


def parse_subuid(text, user):
    """Return [(start, size)] for `user` from /etc/subuid-format text."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, start, size = line.split(":")
        if name == user:
            out.append((int(start), int(size)))
    return out


def intermediate_to_host(i, uid, ranges):
    if i == 0:
        return uid
    k = i - 1
    for start, size in ranges:
        if k < size:
            return start + k
        k -= size
    return None


def container_map(mode, uid, ranges, keep_uid=None):
    """Return [(container_start, intermediate_start, size)]."""
    total = sum(s for _, s in ranges)
    if mode == "host":                  # default rootless: container root is you
        return [(0, 0, 1 + total)]
    if mode == "keep-id":
        cuid = uid if keep_uid is None else keep_uid
        m = []
        if ranges and cuid != 0:
            m.append((0, 1, min(cuid, total)))
        m.append((cuid, 0, 1))
        if total > cuid:
            m.append((cuid + 1, cuid + 1, total - cuid))
        return m
    if mode == "nomap":
        return [(0, 1, total)]
    raise ValueError(mode)


def to_host(container_id, mode, uid, ranges, keep_uid=None):
    for c0, i0, size in container_map(mode, uid, ranges, keep_uid):
        if c0 <= container_id < c0 + size:
            return intermediate_to_host(i0 + container_id - c0, uid, ranges)
    return None                          # unmapped: shows as the overflow id (65534)


def host_to_intermediate(host_id, uid, ranges):
    if host_id == uid:
        return 0
    base = 1
    for start, size in ranges:
        if start <= host_id < start + size:
            return base + host_id - start
        base += size
    return None


def to_container(host_id, mode, uid, ranges, keep_uid=None):
    """Which container ID a host-owned file appears as (None: unmapped, shown as 65534)."""
    i = host_to_intermediate(host_id, uid, ranges)
    if i is None:
        return None
    for c0, i0, size in container_map(mode, uid, ranges, keep_uid):
        if i0 <= i < i0 + size:
            return c0 + i - i0
    return None


SUBUID = "jenya:100000:65536\ngeetha:165536:65536\n"

if __name__ == "__main__":
    r = parse_subuid(SUBUID, "jenya")
    uid = 1000
    for mode in ("host", "keep-id"):
        print(mode, container_map(mode, uid, r))
        for c in (0, 1, 999, 1000, 1001, 65536):
            print(f"  container {c:>5} -> host {to_host(c, mode, uid, r)}")
        print(f"  host file owned by you (1000) appears in the container as {to_container(1000, mode, uid, r)}")
