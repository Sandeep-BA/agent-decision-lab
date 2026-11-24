# Author: Sandeep Belgavi. Original synthetic plan admission example.
from graphlib import TopologicalSorter, CycleError

OPERATIONS = frozenset({"read_fixture", "checksum", "compare"})

def compile_plan(tasks):
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 32:
        raise ValueError("plan must contain 1..32 tasks")
    registry = {}
    for task in tasks:
        if not isinstance(task, dict) or set(task) != {"id", "op", "after"}:
            raise ValueError("invalid task fields")
        name = task["id"]
        if not isinstance(name, str) or not name or name in registry:
            raise ValueError("missing or duplicate task identifier")
        if not isinstance(task["op"], str) or task["op"] not in OPERATIONS:
            raise ValueError("operation is not registered")
        deps = task["after"]
        if not isinstance(deps, list) or any(not isinstance(d, str) for d in deps):
            raise ValueError("predecessors must be strings")
        registry[name] = tuple(deps)
    missing = {d for deps in registry.values() for d in deps} - registry.keys()
    if missing:
        raise ValueError("undeclared predecessors: " + ", ".join(sorted(missing)))
    try:
        return tuple(TopologicalSorter(registry).static_order())
    except CycleError as exc:
        raise ValueError("cyclic proposal") from exc


def run_demo(fixture):
    return list(compile_plan(fixture))

if __name__ == "__main__":
    import json
    from pathlib import Path
    fixture = json.loads(Path(__file__).with_name("sample-input.json").read_text(encoding="utf-8"))
    print(json.dumps(run_demo(fixture),sort_keys=True))
