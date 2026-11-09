# Author: Sandeep Belgavi. Metadata-only policy fixture; no extraction.
from pathlib import PurePosixPath

def validate_entries(entries):
    seen = set()
    for raw_name, kind in entries:
        path = PurePosixPath(raw_name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("unsafe archive path")
        name = str(path).rstrip("/")
        if name in ("", ".") or name in seen:
            raise ValueError("empty or duplicate normalized name")
        if kind not in ("file", "directory"):
            raise ValueError("unsupported archive entry type")
        seen.add(name)
    return seen
