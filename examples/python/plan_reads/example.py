# Author: Sandeep Belgavi. In-memory read-dependency boundary.
from threading import Lock

class Store:
    def __init__(self):
        self.lock = Lock()
        self.rows = {"task": (128, 7), "policy": (512, 3)}

    def snapshot(self):
        with self.lock:
            return dict(self.rows)

    def apply(self, observed, proposed):
        if set(observed) != {"task", "policy"}:
            raise ValueError("incomplete evidence")
        if type(proposed) is not int or proposed < 0:
            raise ValueError("invalid proposed setting")
        with self.lock:
            if any(self.rows[k][1] != observed[k][1] for k in observed):
                return "replan"
            if proposed > self.rows["policy"][0]:
                return "policy-rejected"
            _, version = self.rows["task"]
            self.rows["task"] = (proposed, version + 1)
            return "applied"

store = Store()
evidence = store.snapshot()
with store.lock:
    store.rows["policy"] = (256, 4)
assert store.apply(evidence, 512) == "replan"
assert store.rows["task"] == (128, 7)


def run_demo(fixture):
    store = Store()
    evidence = store.snapshot()
    with store.lock:
        store.rows["policy"] = (fixture["new_ceiling"], 4)
    return {"decision": store.apply(evidence, 512), "task": list(store.rows["task"])}

if __name__ == "__main__":
    import json
    from pathlib import Path
    fixture = json.loads(Path(__file__).with_name("sample-input.json").read_text(encoding="utf-8"))
    print(json.dumps(run_demo(fixture),sort_keys=True))
