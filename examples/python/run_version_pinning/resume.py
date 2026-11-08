# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

"""Deciding what happens to an agent run that resumes after a deploy."""
import json
import sys
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    bundle: str
    checkpoint_schema: int


def resume_action(m, live_bundles, migrations, current_schema):
    """Return (action, reason). Never asks a model; an unknown case always reaches a person."""
    if m.bundle in live_bundles:
        return "pin", f"bundle {m.bundle} is still deployed"
    if (m.checkpoint_schema, current_schema) in migrations:
        return "migrate", f"migration {m.checkpoint_schema}->{current_schema} exists"
    return "close_out", f"no live bundle and no migration for schema {m.checkpoint_schema}"


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/python/run_version_pinning/fixtures/runs.json"
    cfg = json.load(open(path, encoding="utf-8"))
    live, migrations, current = set(cfg["live_bundles"]), {tuple(x) for x in cfg["migrations"]}, cfg["current_schema"]
    for row in cfg["runs"]:
        m = RunManifest(**row)
        action, reason = resume_action(m, live, migrations, current)
        print(m.run_id, action, reason)
