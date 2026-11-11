"""Run leases, a paused worker and an epoch-fenced tool server. Author: Sandeep Belgavi.

Standard library only. Time is a whole number of seconds passed in explicitly, so every
scenario is deterministic. Nothing here calls a model or a real lock service.
"""
from dataclasses import dataclass, field


class StaleEpoch(Exception):
    """Raised by the tool server when a write carries an epoch older than one it has seen."""


@dataclass
class LeaseTable:
    """One lease per run. A grant after expiry increments the epoch (the fencing token)."""
    ttl: int
    owner: dict = field(default_factory=dict)   # run_id -> (worker, epoch, expires_at)

    def acquire(self, run_id, worker, now):
        cur = self.owner.get(run_id)
        if cur and cur[2] > now and cur[0] != worker:
            return None
        epoch = (cur[1] + 1) if cur else 1
        self.owner[run_id] = (worker, epoch, now + self.ttl)
        return epoch

    def renew(self, run_id, worker, epoch, now):
        cur = self.owner.get(run_id)
        if not cur or cur[0] != worker or cur[1] != epoch or cur[2] <= now:
            return False
        self.owner[run_id] = (worker, epoch, now + self.ttl)
        return True


@dataclass
class ToolServer:
    """The resource side. With fencing on, it keeps the highest epoch per run and rejects older ones."""
    fencing: bool
    idempotent: bool = False
    highest: dict = field(default_factory=dict)
    refunds: list = field(default_factory=list)
    status: dict = field(default_factory=dict)
    seen_keys: set = field(default_factory=set)

    def register(self, run_id, epoch):
        self.highest[run_id] = max(self.highest.get(run_id, 0), epoch)

    def refund(self, run_id, epoch, case, worker):
        if self.fencing and epoch < self.highest.get(run_id, 0):
            raise StaleEpoch(f'epoch {epoch} < {self.highest[run_id]}')
        if self.fencing:
            self.register(run_id, epoch)
        self.status[case] = f'refunded by {worker} (epoch {epoch})'
        key = f'{case}/refund'
        if self.idempotent and key in self.seen_keys:
            return 'deduplicated'
        self.seen_keys.add(key)
        self.refunds.append((case, worker, epoch))
        return 'issued'


def scenario(ttl=30, heartbeat=10, pause_at=25, pause=60, reclaim_delay=5, resume_work=20,
             fencing=False, register_on_grant=False, idempotent=False):
    """Worker A starts run R-17 at t=0, renews every `heartbeat` seconds, then stalls at `pause_at`.
    Returns a dict with the event log and the resulting refunds."""
    assert 0 < heartbeat < ttl
    leases, server, log = LeaseTable(ttl), ToolServer(fencing, idempotent), []
    epoch_a = leases.acquire('R-17', 'A', 0)
    t = heartbeat
    while t <= pause_at:
        leases.renew('R-17', 'A', epoch_a, t)
        t += heartbeat
    expiry = leases.owner['R-17'][2]
    wake = pause_at + pause
    events = []
    if wake < expiry:
        events.append((wake, 'A'))
    else:
        grant = expiry + reclaim_delay
        epoch_b = leases.acquire('R-17', 'B', grant)
        log.append(f't={grant}: B acquires R-17 with epoch {epoch_b}')
        if register_on_grant:
            server.register('R-17', epoch_b)
        events += [(grant + resume_work, 'B'), (wake, 'A')]
    for when, who in sorted(events, key=lambda e: (e[0], e[1] != 'B')):
        epoch = epoch_a if who == 'A' else leases.owner['R-17'][1]
        try:
            outcome = server.refund('R-17', epoch, 'CASE-4107', who)
        except StaleEpoch as exc:
            outcome = f'rejected ({exc})'
        log.append(f't={when}: {who} epoch {epoch} -> {outcome}')
    return {'expiry': expiry, 'wake': wake, 'log': log, 'refunds': server.refunds, 'status': server.status}


if __name__ == '__main__':
    for label, kw in [('no fencing', {}), ('fence on write', {'fencing': True}),
                      ('fence on write, B slower', {'fencing': True, 'resume_work': 40}),
                      ('fence on grant, B slower', {'fencing': True, 'register_on_grant': True, 'resume_work': 40})]:
        r = scenario(**kw)
        print(f'{label}: {len(r["refunds"])} refund(s); ' + '; '.join(r['log']))
