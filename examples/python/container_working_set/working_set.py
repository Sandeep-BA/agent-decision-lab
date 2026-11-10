"""Read cgroup v2 memory files and explain what a dashboard "working set" number means.

Author: Sandeep Belgavi. Works on saved copies of memory.current, memory.max and memory.stat.
On a live Linux node you can point it at /sys/fs/cgroup/<path>; the tests use synthetic files only.
"""
from pathlib import Path


def parse_stat(text):
    stats = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].isdigit():
            stats[parts[0]] = int(parts[1])
    return stats


def read_limit(text):
    text = text.strip()
    return None if text == 'max' else int(text)


def analyse(current, limit, stats):
    """Return the numbers needed to tell page cache from memory that cannot be reclaimed."""
    for key in ('anon', 'active_file', 'inactive_file'):
        if key not in stats:
            raise ValueError(f'memory.stat lacks {key}')
    working_set = max(0, current - stats['inactive_file'])
    file_cache = stats['active_file'] + stats['inactive_file']
    report = {
        'usage': current,
        'working_set': working_set,
        'anon': stats['anon'],
        'file_cache': file_cache,
        'inactive_file': stats['inactive_file'],
        'limit': limit,
    }
    if limit is None:
        report['verdict'] = 'no memory.max: the node, not this cgroup, bounds usage'
        return report
    report['working_set_pct'] = round(100 * working_set / limit, 1)
    report['anon_pct'] = round(100 * stats['anon'] / limit, 1)
    if stats['anon'] >= 0.9 * limit:
        report['verdict'] = 'anonymous memory near memory.max: an OOM kill is likely if it grows'
    elif working_set >= 0.9 * limit and stats['anon'] < 0.6 * limit:
        report['verdict'] = 'working set high mostly from active page cache: reclaim before OOM'
    else:
        report['verdict'] = 'headroom available'
    return report


def from_directory(path):
    path = Path(path)
    return analyse(int((path / 'memory.current').read_text().strip()),
                   read_limit((path / 'memory.max').read_text()),
                   parse_stat((path / 'memory.stat').read_text()))


MIB = 1024 * 1024
CACHE_HEAVY = f"""anon {300 * MIB}
file {640 * MIB}
active_file {600 * MIB}
inactive_file {40 * MIB}
shmem 0
"""
ANON_HEAVY = f"""anon {940 * MIB}
file {60 * MIB}
active_file {30 * MIB}
inactive_file {30 * MIB}
shmem 0
"""
