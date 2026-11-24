# Author: Sandeep Belgavi. Synthetic executable trust-closure model.
from dataclasses import dataclass

@dataclass(frozen=True)
class Resource:
    name: str
    owner: str
    mode: int

def audit(resources):
    if not resources:
        return {"allowed": False, "reasons": ["empty execution closure"]}
    reasons = []
    seen = set()
    for item in resources:
        if item.name in seen:
            reasons.append("duplicate resource: " + item.name)
        seen.add(item.name)
        if item.owner != "administrator":
            reasons.append("untrusted owner: " + item.name)
        if item.mode & 0o022:
            reasons.append("shared write access: " + item.name)
    return {"allowed": not reasons, "reasons": reasons}

fixture = [Resource("root", "administrator", 0o755),
           Resource("tools", "administrator", 0o777),
           Resource("server", "administrator", 0o755)]
assert audit(fixture)["allowed"] is False
assert audit([Resource("server", "administrator", 0o755)])["allowed"] is True


def run_demo(fixture):
    return audit([Resource(**item) for item in fixture])

if __name__ == "__main__":
    import json
    from pathlib import Path
    fixture = json.loads(Path(__file__).with_name("sample-input.json").read_text(encoding="utf-8"))
    print(json.dumps(run_demo(fixture),sort_keys=True))
