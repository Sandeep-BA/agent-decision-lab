"""One token budget shared by concurrent agent runs: check-then-spend against reserve-and-settle.

Author: Sandeep Belgavi. Companion to "A Spend Limit Shared by Concurrent Agent Runs" (aicassindra.com).
Runs are threads and the model is a fake client with seeded token usage; no provider is called.
"""
import random
import threading


class FakeResponse:
    def __init__(self, input_tokens, output_tokens, stop_reason):
        self.usage = type('Usage', (), {'input_tokens': input_tokens, 'output_tokens': output_tokens})()
        self.stop_reason = stop_reason


class FakeClient:
    """Returns seeded usage; output is cut at max_tokens, as a provider would."""

    def __init__(self, seed, mean_output=3000, pause=None):
        self.rng, self.mean, self.lock, self.pause = random.Random(seed), mean_output, threading.Lock(), pause

    def create(self, input_tokens, max_tokens):
        with self.lock:
            wanted = max(1, int(self.rng.expovariate(1 / self.mean)))
        if self.pause:
            self.pause.wait()                      # lets tests line up concurrent calls
        out = min(wanted, max_tokens)
        return FakeResponse(input_tokens, out, 'max_tokens' if wanted > max_tokens else 'end_turn')


class CheckThenSpend:
    """The common first version: compare spent with the limit, call, add the usage afterwards."""

    def __init__(self, limit):
        self.limit, self.spent, self.lock = limit, 0, threading.Lock()

    def step(self, client, input_tokens, max_tokens):
        with self.lock:
            if self.spent >= self.limit:
                return None
        r = client.create(input_tokens, max_tokens)  # the gap: others pass the check meanwhile
        with self.lock:
            self.spent += r.usage.input_tokens + r.usage.output_tokens
        return r


class SharedBudget:
    """Reserve input + max_tokens before a call, settle the reported usage after it."""

    def __init__(self, limit):
        self.limit, self.settled, self.reserved, self.lock = limit, 0, 0, threading.Lock()
        self.peak = 0

    def reserve(self, tokens):
        with self.lock:
            if self.settled + self.reserved + tokens > self.limit:
                return None
            self.reserved += tokens
            self.peak = max(self.peak, self.settled + self.reserved)
            return tokens

    def settle(self, hold, actual):
        with self.lock:
            self.reserved -= hold
            self.settled += actual

    @property
    def spent(self):
        return self.settled

    def step(self, client, input_tokens, max_tokens):
        hold = self.reserve(input_tokens + max_tokens)
        if hold is None:
            return None
        used = hold                                # a failed call keeps its full hold
        try:
            r = client.create(input_tokens, max_tokens)
            used = r.usage.input_tokens + r.usage.output_tokens
            return r
        finally:
            self.settle(hold, used)


def run_fleet(policy, runs=12, steps=6, input_tokens=500, max_tokens=8000, seed=20261031, concurrent_start=True):
    """Start `runs` threads that each take up to `steps` steps; return totals and per-run outcomes."""
    barrier = threading.Barrier(runs) if concurrent_start else None
    outcomes, cut = [None] * runs, [0]
    cut_lock = threading.Lock()

    def worker(i):
        client = FakeClient(seed + i)
        if barrier:
            barrier.wait()
        done = 0
        for _ in range(steps):
            r = policy.step(client, input_tokens, max_tokens)
            if r is None:
                break
            if r.stop_reason == 'max_tokens':
                with cut_lock:
                    cut[0] += 1
            done += 1
        outcomes[i] = 'completed' if done == steps else ('refused' if done == 0 else 'stopped mid-way')

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(runs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return {'spent': policy.spent, 'limit': policy.limit, 'over': max(0, policy.spent - policy.limit),
            'completed': outcomes.count('completed'), 'stopped': outcomes.count('stopped mid-way'),
            'refused': outcomes.count('refused'), 'cut_at_max_tokens': cut[0]}


def gap_demo(limit=10000, runs=8):
    """All runs pass the check before any usage is recorded: the deterministic worst case."""
    gate = threading.Event()
    policy = CheckThenSpend(limit)
    clients = [FakeClient(i, mean_output=4000, pause=gate) for i in range(runs)]
    threads = [threading.Thread(target=policy.step, args=(clients[i], 500, 8000)) for i in range(runs)]
    for t in threads:
        t.start()
    while sum(1 for t in threads if t.is_alive()) < runs:
        pass
    gate.set()
    for t in threads:
        t.join()
    return {'limit': limit, 'spent': policy.spent, 'calls': runs}


if __name__ == '__main__':
    print('check_then_spend', run_fleet(CheckThenSpend(150000)))
    print('reserve_per_step', run_fleet(SharedBudget(150000)))
    print('gap_demo        ', gap_demo())
