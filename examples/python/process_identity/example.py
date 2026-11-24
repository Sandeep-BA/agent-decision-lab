# Author: Sandeep Belgavi. Synthetic process ownership decision only.
from dataclasses import dataclass

@dataclass(frozen=True)
class ProcessRecord:
    pid: int
    incarnation: str | None
    owner_generation: str

def cleanup_decision(owned, observed, generation):
    if owned.owner_generation != generation:
        return "reconcile-supervisor-generation"
    if observed is None:
        return "already-gone"
    if owned.incarnation is None or observed.incarnation is None:
        return "refuse-unknown-identity"
    if (owned.pid, owned.incarnation) != (observed.pid, observed.incarnation):
        return "refuse-different-process"
    if observed.owner_generation != generation:
        return "refuse-unowned-process"
    return "eligible-for-bound-handle-cleanup"

owned = ProcessRecord(42, "birth-a", "supervisor-7")
replacement = ProcessRecord(42, "birth-b", "unrelated")
assert cleanup_decision(owned, replacement, "supervisor-7") == "refuse-different-process"
assert cleanup_decision(owned, None, "supervisor-7") == "already-gone"


def run_demo(fixture):
    return {"decision":cleanup_decision(ProcessRecord(**fixture["owned"]),ProcessRecord(**fixture["observed"]),fixture["generation"])}

if __name__ == "__main__":
    import json
    from pathlib import Path
    fixture = json.loads(Path(__file__).with_name("sample-input.json").read_text(encoding="utf-8"))
    print(json.dumps(run_demo(fixture),sort_keys=True))
