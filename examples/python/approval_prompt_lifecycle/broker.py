"""Author: Sandeep Belgavi. An approval broker that treats each prompt as state: one visible
prompt per endpoint key, withdrawal when the request ends, decisions bound to the prompt and
its originating turn, session grants, and a deny-instead-of-prompting mode for unattended runs.
Original model inspired by public release notes; it is not either tool's implementation."""
from collections import OrderedDict, deque
from dataclasses import dataclass


@dataclass
class Request:
    rid: str
    turn: str
    host: str
    port: int = 443
    protocol: str = "https"
    env: str = "local"

    @property
    def key(self):
        return (self.env, self.host, self.protocol, self.port)


class Broker:
    def __init__(self, unattended=False):
        self.unattended = unattended
        self.queues = OrderedDict()        # key -> deque of waiting requests
        self.active = {}                   # key -> (prompt_id, request)
        self.session_grants, self.session_denies = set(), set()
        self.results = {}                  # rid -> allowed | denied | withdrawn
        self.shown = []                    # prompts shown to the person
        self.log = []
        self._n = 0

    def submit(self, req):
        if req.key in self.session_grants:
            self.results[req.rid] = "allowed"; self.log.append(f"{req.rid}: session grant for {req.host}:{req.port}"); return
        if req.key in self.session_denies:
            self.results[req.rid] = "denied"; self.log.append(f"{req.rid}: session deny rule"); return
        if self.unattended:
            self.results[req.rid] = "denied"; self.log.append(f"{req.rid}: would need a prompt; denied instead, turn continues"); return
        self.queues.setdefault(req.key, deque()).append(req)
        self._advance(req.key)

    def _advance(self, key):
        if key in self.active or not self.queues.get(key):
            return
        req = self.queues[key].popleft()
        if req.key in self.session_grants:
            self.results[req.rid] = "allowed"; self.log.append(f"{req.rid}: dequeued, covered by session grant"); return self._advance(key)
        self._n += 1
        pid = f"p{self._n}"
        self.active[key] = (pid, req)
        self.shown.append((pid, req.rid))
        self.log.append(f"{pid}: prompt shown for {req.rid} ({req.host}:{req.port}, turn {req.turn})")

    def request_ended(self, rid):
        for key, (pid, req) in list(self.active.items()):
            if req.rid == rid:
                del self.active[key]
                self.results[rid] = "withdrawn"
                self.log.append(f"{pid}: withdrawn because {rid} ended")
                self._advance(key)
                return
        for q in self.queues.values():
            for req in list(q):
                if req.rid == rid:
                    q.remove(req); self.results[rid] = "withdrawn"; self.log.append(f"{rid}: removed from queue")

    def decide(self, pid, decision, current_turn):
        """decision: allow-once | deny-once | allow-session | deny-session. Returns True if applied."""
        match = [(k, r) for k, (p, r) in self.active.items() if p == pid]
        if not match:
            self.log.append(f"{pid}: decision '{decision}' rejected, prompt no longer live"); return False
        key, req = match[0]
        if req.turn != current_turn:
            self.log.append(f"{pid}: decision rejected, prompt belongs to turn {req.turn}"); return False
        del self.active[key]
        allowed = decision.startswith("allow")
        self.results[req.rid] = "allowed" if allowed else "denied"
        if decision == "allow-session":
            self.session_grants.add(key)
        if decision == "deny-session":
            self.session_denies.add(key)
        self.log.append(f"{pid}: {decision} for {req.rid}")
        # Waiting requests covered by a new session rule resolve without a prompt.
        for waiting in list(self.queues.get(key, [])):
            if key in self.session_grants or key in self.session_denies:
                self.queues[key].remove(waiting)
                self.results[waiting.rid] = "allowed" if key in self.session_grants else "denied"
                self.log.append(f"{waiting.rid}: resolved by session rule without a prompt")
        self._advance(key)
        return True


def demo(unattended=False):
    b = Broker(unattended)
    for i in range(3):
        b.submit(Request(f"r{i+1}", "t1", "registry.npmjs.org"))
    b.submit(Request("r4", "t1", "catalog.example.test"))
    return b


if __name__ == "__main__":
    b = demo()
    b.decide("p1", "allow-once", "t1")
    b.request_ended("r3")
    b.decide("p3", "allow-session", "t1")
    b.decide("p2", "allow-once", "t1")
    print("\n".join(b.log)); print(b.results)
