"""Evaluate a conversational agent with a simulated user: goal scripts, stop rules, end-state checks,
pass^k, and attributing each failure to the agent or to the simulator.

Author: Sandeep Belgavi. Offline companion to "Evaluating a Conversational Agent With a Simulated User"
(aicassindra.com). The simulator and both agents are small deterministic rule programs with a seeded
random source; no model is called. They stand in for LLM-backed components to show the evaluation logic.
"""
import itertools
import json
import random
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOKINGS = {"QX7P2": {"surname": "Rao", "date": "2026-11-03", "hours_to_departure": 52},
            "LM4K9": {"surname": "Osei", "date": "2026-10-27", "hours_to_departure": 10},
            "ZT8W1": {"surname": "Haddad", "date": "2026-11-12", "hours_to_departure": 260}}
POLICY_HOURS = 24          # no date change within 24 hours of departure
MAX_TURNS = 8              # user turns, including the first message


class SimUser:
    """Holds a goal and private facts; reveals facts per persona; may drift (a simulator fault)."""
    def __init__(self, task, persona, rng, drift):
        self.task, self.persona, self.rng, self.drift = task, persona, rng, drift
        self.said = []                                     # every fact value the user stated

    def say(self, key):
        value = self.task["facts"][key]
        if key == "new_date" and self.rng.random() < self.drift:
            value = "2026-12-24"                           # invented: not in the goal script
        self.said.append((key, value))
        return {key: value}

    def first_message(self):
        msg = {"intent": "change_date"}
        for k in ("reference", "surname", "new_date"):
            if self.persona == "detailed" or (self.persona == "mixed" and self.rng.random() < 0.5):
                msg.update(self.say(k))                    # volunteered up front
        return msg

    def answer(self, asked):
        return self.say(asked) if asked in self.task["facts"] else {"unknown": asked}


def agent_turns(user, first, careful):
    """A date-change agent. `careful=False` has a bug: it skips the 24-hour policy check when the
    new date arrives in the first message instead of in answer to its own question."""
    db_change, known, turns = None, dict(first), 1
    while turns < MAX_TURNS:
        missing = [k for k in ("reference", "surname", "new_date") if k not in known]
        if not missing:
            break
        known.update(user.answer(missing[0]))
        turns += 1
    else:
        return {"outcome": "stopped: turn limit", "change": None, "turns": turns}
    booking = BOOKINGS.get(known["reference"])
    if not booking or booking["surname"] != known["surname"]:
        return {"outcome": "refused: verification failed", "change": None, "turns": turns}
    date_was_asked = "new_date" not in first
    if (careful or date_was_asked) and booking["hours_to_departure"] < POLICY_HOURS:
        return {"outcome": "refused: inside 24 hours", "change": None, "turns": turns}
    db_change = (known["reference"], known["new_date"])
    return {"outcome": "changed", "change": db_change, "turns": turns}


def simulator_followed_script(user):
    """Adherence check on the simulator itself: every stated fact must come from the goal script."""
    return all(user.task["facts"].get(k) == v for k, v in user.said)


def run(tasks, persona, careful, trials=4, drift=0.0, seed=11):
    rng = random.Random(seed)
    per_task, failures = [], {"agent": 0, "simulator": 0}
    for task in tasks:
        successes = 0
        for _ in range(trials):
            user = SimUser(task, persona, rng, drift)
            result = agent_turns(user, user.first_message(), careful)
            ok = result["change"] == task["expected_change"]       # judge the end state, not the words
            if ok:
                successes += 1
            elif simulator_followed_script(user):
                failures["agent"] += 1
            else:
                failures["simulator"] += 1                          # discard and re-run, do not blame the agent
        per_task.append(successes)
    n, k = trials, trials
    return {"persona": persona, "careful": careful, "drift": drift, "trials": trials,
            "pass^1": round(sum(c / n for c in per_task) / len(tasks), 3),
            "pass^k": round(sum(comb(c, k) / comb(n, k) for c in per_task) / len(tasks), 3),
            "failures": failures, "successes_per_task": per_task}


def load_tasks():
    tasks = json.loads((HERE / "fixtures" / "tasks.json").read_text(encoding="utf-8"))
    for t in tasks:
        t["expected_change"] = tuple(t["expected_change"]) if t["expected_change"] else None
    return tasks


def main():
    tasks = load_tasks()
    for persona, careful in itertools.product(("waits", "detailed", "mixed"), (False, True)):
        print(json.dumps(run(tasks, persona, careful)))
    print(json.dumps(run(tasks, "detailed", True, drift=0.25)))


if __name__ == "__main__":
    main()
