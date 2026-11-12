"""Author: Sandeep Belgavi. Offline model of an at-least-once queue (SQS-style visibility
timeout, receipt handles, ChangeMessageVisibility heartbeats, maxReceiveCount redrive)
feeding a slow agent step. Synthetic: whole seconds, one message, consumers always polling."""
from dataclasses import dataclass, field


@dataclass
class Result:
    receives: list = field(default_factory=list)      # (time, consumer, handle)
    replies: int = 0                                  # customer-visible effects
    suppressed: int = 0                               # effects stopped by the idempotency key
    outcome: str = "in-flight"                        # deleted | dead-letter | in-flight
    model_seconds: int = 0                            # model time spent on all attempts
    trace: list = field(default_factory=list)


def simulate(visibility=30, step=45, heartbeat=0, max_receives=5, idempotency_key=False, horizon=900):
    if not (1 <= visibility <= 43200 and 1 <= step <= 3600 and 0 <= heartbeat <= 3600 and 1 <= max_receives <= 1000):
        raise ValueError("input out of range")
    r = Result()
    names = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    t, count, deleted, dlq = 0, 0, False, False
    latest = None
    effect_done = False
    attempts = []                                     # (start, consumer, handle, expiry_holder)
    while t <= horizon and not deleted and not dlq:
        count += 1
        who = names[(count - 1) % 26]
        handle = f"h{count}"
        latest = handle
        r.receives.append((t, who, handle))
        r.trace.append(f"t={t} s: consumer {who} receives the message (receive count {count}, handle {handle}).")
        expiry = t + visibility
        if heartbeat:
            beat = t + heartbeat
            while beat < t + step and beat < expiry:
                expiry = beat + visibility
                beat += heartbeat
            if beat < t + step and beat >= expiry:
                r.trace.append(f"t={expiry} s: the visibility timeout expires before {who}'s next heartbeat at t={beat} s.")
        finish = t + step
        attempts.append((t, who, handle, finish))
        if finish < expiry:
            # The step completes while this receive still owns the message.
            r.model_seconds += step
            effect_done = _effect(r, finish, who, idempotency_key, effect_done)
            r.trace.append(f"t={finish} s: {who} deletes with {handle}, the latest handle, so the message is removed.")
            deleted = True
            r.outcome = "deleted"
            break
        # The message reappears at expiry; another consumer is already polling.
        if count >= max_receives:
            r.trace.append(f"t={expiry} s: receive count {count} has reached maxReceiveCount {max_receives}; the queue moves the message to the dead-letter queue.")
            dlq = True
            r.outcome = "dead-letter"
        t = expiry
    # Finish every earlier attempt that was still running when ownership moved on.
    for start, who, handle, finish in attempts:
        if r.outcome == "deleted" and handle == latest:
            continue
        if finish > horizon:
            continue
        r.model_seconds += step
        effect_done = _effect(r, finish, who, idempotency_key, effect_done)
        reason = "the message is already in the dead-letter queue" if r.outcome == "dead-letter" and handle == latest else \
                 "the message has already been deleted" if r.outcome == "deleted" else f"{handle} is no longer the latest handle"
        r.trace.append(f"t={finish} s: {who} tries to delete with {handle}; not removed because {reason}.")
    r.trace.sort(key=lambda s: int(s.split(' ', 1)[0][2:]))
    r.trace.insert(0, f"Setup: visibility timeout {visibility} s, agent step {step} s, heartbeat {'every %d s' % heartbeat if heartbeat else 'off'}, maxReceiveCount {max_receives}, idempotency key {'on' if idempotency_key else 'off'}.")
    r.trace.append(f"Outcome: {r.outcome}; {len(r.receives)} receives, {r.replies} customer replies, {r.model_seconds} model-seconds.")
    return r


def _effect(r, when, who, keyed, done):
    if keyed and done:
        r.suppressed += 1
        r.trace.append(f"t={when} s: {who} finishes the step; the reply service already holds this idempotency key, so no second reply is sent.")
        return True
    r.replies += 1
    r.trace.append(f"t={when} s: {who} finishes the step and the customer receives reply {r.replies}.")
    return True


if __name__ == "__main__":
    for kw in [{}, {"heartbeat": 10}, {"heartbeat": 30}, {"visibility": 60}, {"idempotency_key": True}]:
        res = simulate(**kw)
        print(kw, res.outcome, len(res.receives), res.replies, res.model_seconds)
        for line in res.trace:
            print("   ", line)
