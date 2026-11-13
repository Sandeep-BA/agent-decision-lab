"""An agent runtime embedded in a host that owns capacity, capabilities and identity.

Author: Sandeep Belgavi. Original teaching model inspired by the shape of three
Codex changes that shipped in rust-v0.168.0 (host-owned turn admission, a
restriction marker for root-only capabilities, an inherited root session id).
It does not use or reproduce Codex code; no model is called.
"""
from dataclasses import dataclass, field

ROOT_ONLY = {"ask_user", "install_plugin", "message_user_async", "approve_mcp_tool"}
ALWAYS = {"read_case", "draft_reply"}


class AdmissionDenied(Exception):
    pass


class HostAdmission:
    """Host-side capacity: a fixed number of execution slots."""

    def __init__(self, slots):
        self.slots = slots
        self.in_use = 0
        self.log = []

    def acquire(self, thread_id):
        if self.in_use >= self.slots:
            self.log.append(f"deny {thread_id}: {self.in_use}/{self.slots} slots in use")
            raise AdmissionDenied(thread_id)
        self.in_use += 1
        self.log.append(f"admit {thread_id}: {self.in_use}/{self.slots}")
        return Guard(self, thread_id)


class Guard:
    def __init__(self, host, thread_id):
        self.host, self.thread_id, self.open = host, thread_id, True

    def release(self):
        if self.open:
            self.open = False
            self.host.in_use -= 1
            self.host.log.append(f"release {self.thread_id}: {self.host.in_use}/{self.host.slots}")


@dataclass
class Thread:
    thread_id: str
    kind: str = "fresh"            # fresh | resumed | forked | native_child
    restricted: bool = False
    session_id: str = ""
    pending_input: list = field(default_factory=list)
    transcript: list = field(default_factory=list)

    def tools(self):
        return sorted(ALWAYS if self.restricted else ALWAYS | ROOT_ONLY)


def start_thread(thread_id, kind="fresh", restrict_root_capabilities=False, inherited_session_id=None):
    """Startup data is captured once. An inherited session id is only for a fresh child."""
    if inherited_session_id is not None:
        if kind != "fresh":
            raise ValueError(f"inherited session id rejected for a {kind} thread")
        if inherited_session_id == thread_id:
            raise ValueError("inherited session id must differ from the thread id")
    return Thread(thread_id, kind, restrict_root_capabilities, inherited_session_id or thread_id)


def cold_resume(saved, restrict_root_capabilities=False):
    """The restriction is not persisted by the runtime: the host must supply it again."""
    t = Thread(saved["thread_id"], "resumed", restrict_root_capabilities, saved["session_id"])
    t.transcript = list(saved["transcript"])
    return t


def submit(thread, host, text):
    """Record accepted input before admission, so a denial never loses it."""
    thread.pending_input.append(text)
    try:
        guard = host.acquire(thread.thread_id)
    except AdmissionDenied:
        thread.transcript.append(("system", "turn not admitted; input kept for the next turn"))
        return "denied"
    try:
        while thread.pending_input:
            thread.transcript.append(("user", thread.pending_input.pop(0)))
        thread.transcript.append(("agent", f"handled with tools {thread.tools()}"))
        return "ran"
    finally:
        guard.release()


def call_tool(thread, name):
    if name not in thread.tools():
        return f"refused: {name} is root-only and this thread is restricted"
    return f"ok: {name}"


if __name__ == "__main__":
    host = HostAdmission(slots=1)
    worker = start_thread("thr-jenya-2", restrict_root_capabilities=True, inherited_session_id="sess-geetha-1")
    print("session id", worker.session_id, "tools", worker.tools())
    print(call_tool(worker, "ask_user"))
    hold = host.acquire("thr-other")
    print(submit(worker, host, "Summarise CASE-6120"), worker.pending_input)
    hold.release()
    print(submit(worker, host, "and CASE-6121"), worker.transcript[-2:])
    saved = {"thread_id": worker.thread_id, "session_id": worker.session_id, "transcript": worker.transcript}
    forgot = cold_resume(saved)
    print("resume without marker:", call_tool(forgot, "install_plugin"))
    print("resume with marker:", call_tool(cold_resume(saved, True), "install_plugin"))
    for kw in ({"kind": "forked"}, {}):
        try:
            start_thread("thr-x", inherited_session_id="thr-x" if not kw else "sess-1", **kw)
        except ValueError as e:
            print("rejected:", e)
    print("\n".join(host.log))
