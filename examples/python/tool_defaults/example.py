# Author: Sandeep Belgavi. Explicit, versioned tool argument normalization.
DEFAULTS = {1: {"limit": 20, "detail": False},
            2: {"limit": 40, "detail": False}}

def normalize(proposal, version=1):
    if not isinstance(proposal, dict):
        raise ValueError("arguments must be an object")
    if type(version) is not int or version not in DEFAULTS:
        raise ValueError("unknown normalization version")
    if set(proposal) - {"limit", "detail"}:
        raise ValueError("unknown argument")
    effective = dict(DEFAULTS[version])
    effective.update(proposal)
    if type(effective["limit"]) is not int or not 1 <= effective["limit"] <= 100:
        raise ValueError("limit must be an integer in 1..100")
    if type(effective["detail"]) is not bool:
        raise ValueError("detail must be a boolean")
    return {"normalization_version": version, "arguments": effective}

proposal = {"detail": False}
accepted = normalize(proposal)
assert accepted["arguments"] == {"limit": 20, "detail": False}
assert proposal == {"detail": False}
assert normalize({}, 2)["arguments"]["limit"] == 40


def run_demo(fixture):
    return normalize(fixture["proposal"], fixture["version"])

if __name__ == "__main__":
    import json
    from pathlib import Path
    fixture = json.loads(Path(__file__).with_name("sample-input.json").read_text(encoding="utf-8"))
    print(json.dumps(run_demo(fixture),sort_keys=True))
