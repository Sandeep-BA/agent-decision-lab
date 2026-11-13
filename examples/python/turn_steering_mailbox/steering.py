"""Messages sent to a running agent turn: admission, delivery boundaries, the close race.

Author: Sandeep Belgavi. Original teaching model; the scripted "model" below is a
list of planned steps, not a provider call. Interleavings are explicit so the
race is reproducible without threads.
"""


class Turn:
    """One turn. A steer is accepted while admission is open and is delivered
    only at a boundary: before the next model sample, never in the middle of a
    tool call. Tool calls planned before a steer arrived are stale and dropped
    if the steer is delivered before they run."""

    def __init__(self, plan, atomic_close=True):
        self.plan = list(plan)          # e.g. ["sample", "tool:lookup", "sample", "final"]
        self.atomic_close = atomic_close
        self.admission_open = True
        self.mailbox = []
        self.delivered = []
        self.executed = []
        self.next_task = []
        self.lost = []
        self.log = []
        self.state = "running"

    def steer(self, text):
        if self.admission_open:
            self.mailbox.append(text)
            self.log.append(f"accepted steer {text!r}")
            return "accepted"
        self.next_task.append(text)
        self.log.append(f"turn closing: {text!r} queued for the next task")
        return "queued"

    def _deliver(self):
        if not self.mailbox:
            return False
        self.delivered.extend(self.mailbox)
        self.log.append(f"deliver at boundary: {self.mailbox}")
        self.mailbox.clear()
        stale = [s for s in self.plan if s.startswith("tool:")]
        if stale:
            self.log.append(f"drop stale tool calls {stale}")
        self.plan = ["sample", "final"]
        return True

    def step(self):
        """Run one planned step. Returns False when the turn has ended."""
        if self.state != "running":
            return False
        if not self.plan:
            return self._finish()
        self._deliver()                          # boundary: before every step
        action = self.plan[0]
        if action == "sample" or action == "final":
            action = self.plan.pop(0)
            self.executed.append(action)
            self.log.append(f"model {action}")
            if action == "final":
                return self._finish()
            return True
        self.plan.pop(0)
        self.executed.append(action)
        self.log.append(f"run {action}")
        return True

    def _finish(self):
        """The final transcript flush. `on_flush` runs while the flush is in
        progress, which is where a steer can arrive."""
        if self.atomic_close:
            if self.on_flush:
                self.on_flush(self)
                self.on_flush = None
            # One step: close admission and look at the mailbox together.
            self.admission_open = False
            if self.mailbox:
                self.log.append("pending input found while closing: resume sampling in the same turn")
                self.admission_open = True
                self._deliver()
                return True
        else:
            had_input = bool(self.mailbox)       # check first ...
            if self.on_flush:
                self.on_flush(self)              # ... a steer is accepted here ...
                self.on_flush = None
            self.admission_open = False          # ... then close
            if had_input:
                self.admission_open = True
                self._deliver()
                return True
            if self.mailbox:
                self.lost.extend(self.mailbox)
                self.log.append(f"LOST: accepted {self.mailbox} after the pending-input check")
                self.mailbox.clear()
        self.state = "done"
        self.log.append("turn complete")
        return False

    on_flush = None


def run(turn, steers_at=None, limit=50):
    """Run to completion; `steers_at` maps step index -> steer text."""
    steers_at = steers_at or {}
    i = 0
    while i < limit:
        if i in steers_at:
            turn.steer(steers_at[i])
        if not turn.step():
            break
        i += 1
    return turn


if __name__ == "__main__":
    plan = ["sample", "tool:lookup_order", "tool:draft_refund", "sample", "final"]
    t = run(Turn(plan), {1: "Only CASE-7031, not CASE-7030"})
    print("steer mid-turn:", t.executed, "delivered", t.delivered)
    for atomic in (False, True):
        t = Turn(["sample", "final"], atomic_close=atomic)
        t.on_flush = lambda tt: tt.steer("Also mention the return window")
        run(t)
        print("atomic close" if atomic else "check-then-close", "| executed", t.executed, "| delivered", t.delivered, "| lost", t.lost)
    t = run(Turn(["sample", "final"]))
    print("after final:", t.steer("Tomorrow, check CASE-7032"), t.next_task)
