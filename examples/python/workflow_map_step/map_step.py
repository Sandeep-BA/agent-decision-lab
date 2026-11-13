"""Discrete-time model of a workflow map step that runs one child per list item.

Author: Sandeep Belgavi. Original teaching model; no workflow engine or model is called.

Each item has a duration (whole seconds) and an outcome: "ok", "fail" or "input"
(the child asks a person for input and pauses). Items start in input order, at
most `workers` at a time. Policies:

- fail_fast: the first failure cancels running items, starts nothing else and
  fails the step (the shape ADK Java's experimental ParallelWorkers documents).
- collect: a failure is recorded as that item's result; the others continue.

An "input" outcome stops queued items from starting; running items finish and
the step pauses. A crash at `crash_at` loses running work. On resume, items
whose results were checkpointed are skipped when `checkpoint` is true;
otherwise every item runs again.
"""
from dataclasses import dataclass, field


@dataclass
class Item:
    key: str
    duration: int
    outcome: str = "ok"


@dataclass
class Run:
    status: str = "running"
    finished_at: int = 0
    results: dict = field(default_factory=dict)
    starts: int = 0
    cancelled: list = field(default_factory=list)
    wasted_seconds: int = 0
    trace: list = field(default_factory=list)


def run_map(items, workers, policy="fail_fast", checkpoint=True, crash_at=None, done=None, clock=0):
    """Run once. `done` holds checkpointed results from an earlier attempt."""
    if workers < 1:
        raise ValueError("workers must be at least 1")
    if policy not in ("fail_fast", "collect"):
        raise ValueError("unknown policy")
    run = Run()
    done = dict(done or {})
    queue = [it for it in items if it.key not in done]
    for key in done:
        run.results[key] = done[key]
        run.trace.append((clock, f"skip {key}: checkpointed result {done[key]}"))
    running = {}  # key -> (item, start)
    t = clock
    gate_open = True
    while True:
        while gate_open and queue and len(running) < workers:
            it = queue.pop(0)
            running[it.key] = (it, t)
            run.starts += 1
            run.trace.append((t, f"start {it.key} ({it.duration} s)"))
        if not running:
            break
        next_end = min(start + it.duration for it, start in running.values())
        if crash_at is not None and crash_at < next_end:
            t = crash_at
            for key, (it, start) in sorted(running.items()):
                run.wasted_seconds += t - start
                run.trace.append((t, f"crash: lost {key} after {t - start} s"))
            run.status = "crashed"
            run.finished_at = t
            return run
        t = next_end
        ended = sorted(k for k, (it, start) in running.items() if start + it.duration == t)
        for key in ended:
            it, start = running.pop(key)
            if it.outcome == "ok":
                run.results[key] = "ok"
                run.trace.append((t, f"finish {key}: ok" + ("; checkpointed" if checkpoint else "")))
            elif it.outcome == "input":
                run.results[key] = "needs input"
                gate_open = False
                run.trace.append((t, f"{key} asks for input: queued items will not start"))
            else:
                run.results[key] = "error"
                run.trace.append((t, f"finish {key}: error"))
                if policy == "fail_fast":
                    for other, (oit, ostart) in sorted(running.items()):
                        run.wasted_seconds += t - ostart
                        run.cancelled.append(other)
                        run.results[other] = "cancelled"
                        run.trace.append((t, f"cancel {other} after {t - ostart} s"))
                    running.clear()
                    run.status = "failed"
                    run.finished_at = t
                    return run
    run.finished_at = t
    if not gate_open:
        run.status = "paused for input"
    elif any(v == "error" for v in run.results.values()):
        run.status = "completed with errors"
    else:
        run.status = "completed"
    return run


def crash_and_resume(items, workers, policy, checkpoint, crash_at):
    first = run_map(items, workers, policy, checkpoint, crash_at)
    if first.status != "crashed":
        return first, None
    kept = {k: v for k, v in first.results.items()} if checkpoint else {}
    second = run_map(items, workers, policy, checkpoint, None, kept, clock=crash_at)
    return first, second


def ordered(items, run):
    return [run.results.get(it.key, "not run") for it in items]


CASES = [Item(f"CASE-51{n:02d}", d) for n, d in zip(range(1, 9), [4, 7, 3, 9, 5, 6, 2, 8])]


if __name__ == "__main__":
    for title, kw in [("3 workers, all ok", {}), ("1 worker", {"workers": 1})]:
        r = run_map(CASES, kw.get("workers", 3))
        print(title, r.status, "t =", r.finished_at, "starts =", r.starts)
    failing = [Item(i.key, i.duration, "fail" if i.key == "CASE-5104" else "ok") for i in CASES]
    for policy in ("fail_fast", "collect"):
        r = run_map(failing, 3, policy)
        print("CASE-5104 fails,", policy, r.status, "t =", r.finished_at, "cancelled =", r.cancelled, "wasted =", r.wasted_seconds, ordered(failing, r))
    for cp in (True, False):
        a, b = crash_and_resume(CASES, 3, "fail_fast", cp, 12)
        print("crash at 12 s, checkpoint =", cp, "| first:", sorted(k for k, v in a.results.items()), "| resume starts =", b.starts, "finished at", b.finished_at, "total starts =", a.starts + b.starts)
    asking = [Item(i.key, i.duration, "input" if i.key == "CASE-5103" else "ok") for i in CASES]
    r = run_map(asking, 3)
    print("CASE-5103 asks for input:", r.status, "t =", r.finished_at, ordered(asking, r))
