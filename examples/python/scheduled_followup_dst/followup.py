"""Scheduled follow-ups stored as wall-clock intent plus an IANA zone, resolved at fire time.

Author: Sandeep Belgavi. Companion to "When an Agent Schedules Work for Later" (aicassindra.com).
Synthetic cases for Belgavi's Book Store; no scheduler, database, model or network is used.
Needs the IANA database: on Windows install the pinned tzdata package from requirements.txt.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class FollowUp:
    case_id: str
    local_time: datetime          # naive wall-clock time the customer agreed to
    zone: str                     # IANA name, never an offset
    repeated: str = 'earlier'     # 'earlier' or 'later' for an hour that happens twice
    missing: str = 'forward'      # 'forward' or 'skip' for an hour that does not exist

    def __post_init__(self):
        if self.local_time.tzinfo is not None:
            raise ValueError('store the wall-clock time without an offset; the zone is separate')
        if self.repeated not in ('earlier', 'later') or self.missing not in ('forward', 'skip'):
            raise ValueError('unknown policy')
        ZoneInfo(self.zone)       # raises for an unknown zone name


def classify(f):
    """'ordinary', 'repeated' or 'missing' for the follow-up's local time in its zone."""
    tz = ZoneInfo(f.zone)
    a = f.local_time.replace(tzinfo=tz, fold=0).astimezone(timezone.utc)
    b = f.local_time.replace(tzinfo=tz, fold=1).astimezone(timezone.utc)
    if a == b:
        return 'ordinary'
    return 'repeated' if a.astimezone(tz).replace(tzinfo=None) == f.local_time else 'missing'


def due_instant(f):
    """The UTC instant to fire at, or None when the local time does not exist and the policy is skip."""
    tz = ZoneInfo(f.zone)
    a = f.local_time.replace(tzinfo=tz, fold=0).astimezone(timezone.utc)
    b = f.local_time.replace(tzinfo=tz, fold=1).astimezone(timezone.utc)
    kind = classify(f)
    if kind == 'ordinary':
        return a
    if kind == 'repeated':
        return min(a, b) if f.repeated == 'earlier' else max(a, b)
    return None if f.missing == 'skip' else max(a, b)


def naive_instant(f, stored_at):
    """The bug: convert once with the offset in force when the follow-up was stored."""
    offset = stored_at.astimezone(ZoneInfo(f.zone)).utcoffset()
    return (f.local_time - offset).replace(tzinfo=timezone.utc)


class Runner:
    """Fires due follow-ups once each, after checking the precondition in the system of record."""

    def __init__(self, case_still_pending, send):
        self.case_still_pending, self.send, self.sent_keys, self.log = case_still_pending, send, set(), []

    def run_once(self, f, now):
        due = due_instant(f)
        if due is None:
            outcome = 'skipped: local time does not exist'
        elif now < due:
            outcome = 'not due'
        elif not self.case_still_pending(f.case_id):
            outcome = 'skipped: precondition no longer holds'
        else:
            key = (f.case_id, f.local_time.isoformat())
            if key in self.sent_keys:
                outcome = 'duplicate suppressed'
            else:
                self.sent_keys.add(key)
                self.send(f)
                outcome = 'sent'
        self.log.append((f.case_id, outcome))
        return outcome


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def demo():
    stored = utc(2026, 10, 21, 14, 32)
    london = FollowUp('CASE-5104', datetime(2026, 11, 1, 14, 30), 'Europe/London')
    ny_night = FollowUp('CASE-5121', datetime(2026, 11, 1, 1, 30), 'America/New_York')
    ny_gap = FollowUp('CASE-5122', datetime(2027, 3, 14, 2, 30), 'America/New_York')
    rows = [
        ('london_naive', naive_instant(london, stored).isoformat()),
        ('london_resolved', due_instant(london).isoformat()),
        ('ny_repeated_earlier', due_instant(ny_night).isoformat()),
        ('ny_repeated_later', due_instant(FollowUp('CASE-5121', ny_night.local_time, ny_night.zone, repeated='later')).isoformat()),
        ('ny_missing_forward', due_instant(ny_gap).astimezone(ZoneInfo('America/New_York')).isoformat()),
        ('ny_missing_skip', str(due_instant(FollowUp('CASE-5122', ny_gap.local_time, ny_gap.zone, missing='skip')))),
    ]
    open_cases = {'CASE-5104'}
    sent = []
    runner = Runner(lambda case: case in open_cases, sent.append)
    now = utc(2026, 11, 1, 15, 0)
    rows.append(('runner_first', runner.run_once(london, now)))
    rows.append(('runner_retry', runner.run_once(london, now)))
    open_cases.clear()
    rows.append(('runner_closed', runner.run_once(FollowUp('CASE-5104', datetime(2026, 11, 2, 9, 0), 'Europe/London'), utc(2026, 11, 2, 10, 0))))
    return rows


if __name__ == '__main__':
    for name, value in demo():
        print('%-22s %s' % (name, value))
