"""Author: Sandeep Belgavi. Estimate when an agent loop in a durable workflow reaches event history limits.

A help-desk conversation for the fictional Belgavi's Book Store runs as one workflow: every customer
message arrives as a signal, the model call is an activity, and tool calls are activities. The model
counts history events and payload bytes per turn under two designs and shows where continue-as-new
must happen. Limits are the documented Temporal defaults (51,200 events or 50 MB; warnings at 10,240
events or 10 MB; 2 MB per payload). Event counts per command follow the usual scheduled/started/
completed pattern and are an approximation; real counts depend on SDK batching of workflow tasks.

No workflow engine, model or network is called.
"""
import json
from dataclasses import dataclass, asdict

EVENT_LIMIT, EVENT_WARN = 51_200, 10_240
SIZE_LIMIT, SIZE_WARN = 50 * 1024 * 1024, 10 * 1024 * 1024
PAYLOAD_LIMIT = 2 * 1024 * 1024


@dataclass(frozen=True)
class Turn:
    user_bytes: int = 400          # customer message carried by the signal
    model_out_bytes: int = 1_500   # model reply and tool requests (activity result)
    tools: int = 2                 # tool activities per turn, run in parallel
    tool_args_bytes: int = 200
    tool_result_bytes: int = 3_000


def events_per_turn(t: Turn) -> int:
    signal = 1 + 3                       # WorkflowExecutionSignaled + one workflow task
    model = 3 + 3                        # activity scheduled/started/completed + workflow task
    tools = 3 * t.tools + (3 if t.tools else 0)   # parallel tools finish into one workflow task
    return signal + model + tools


def transcript_growth(t: Turn) -> int:
    return t.user_bytes + t.model_out_bytes + t.tools * (t.tool_args_bytes + t.tool_result_bytes)


def bytes_for_turn(t: Turn, turn_index: int, inline_transcript: bool) -> int:
    """History bytes added by one turn. turn_index starts at 1."""
    base = transcript_growth(t)
    model_input = transcript_growth(t) * (turn_index - 1) + t.user_bytes if inline_transcript else t.user_bytes + 64
    return base + model_input


def first_limit(t: Turn, inline_transcript: bool, max_turns: int = 100_000):
    events = size = 0
    warned = None
    for n in range(1, max_turns + 1):
        model_input = transcript_growth(t) * (n - 1) + t.user_bytes if inline_transcript else t.user_bytes + 64
        if model_input > PAYLOAD_LIMIT:
            return {"turn": n, "limit": "payload 2 MB", "events": events, "bytes": size, "first_warning": warned}
        events += events_per_turn(t)
        size += bytes_for_turn(t, n, inline_transcript)
        if warned is None and (events >= EVENT_WARN or size >= SIZE_WARN):
            warned = {"turn": n, "by": "events" if events >= EVENT_WARN else "size"}
        if events >= EVENT_LIMIT:
            return {"turn": n, "limit": "events", "events": events, "bytes": size, "first_warning": warned}
        if size >= SIZE_LIMIT:
            return {"turn": n, "limit": "size", "events": events, "bytes": size, "first_warning": warned}
    return {"turn": None, "limit": None, "events": events, "bytes": size, "first_warning": warned}


@dataclass
class CarriedState:
    """What crosses a continue-as-new boundary. Effect keys use the case id and turn, never the run id."""
    case_id: str
    next_turn: int
    transcript_ref: str
    summary: str
    completed_effect_keys: tuple
    pending_approval: str | None


def effect_key(case_id: str, turn: int, tool: str) -> str:
    return f"{case_id}:turn-{turn}:{tool}"


def chain(t: Turn, total_turns: int, can_every: int, case_id: str = "CASE-7731"):
    """Simulate continue-as-new every can_every turns with reference transcripts."""
    runs, state, executed = [], CarriedState(case_id, 1, f"store://{case_id}/transcript", "", (), None), []
    while state.next_turn <= total_turns:
        start = state.next_turn
        end = min(total_turns, start + can_every - 1)
        events = 2  # WorkflowExecutionStarted + first workflow task scheduled, roughly
        keys = list(state.completed_effect_keys)
        for n in range(start, end + 1):
            events += events_per_turn(t)
            k = effect_key(case_id, n, "add_case_note")
            if k not in keys:          # an idempotent effect: replay after a boundary must not repeat it
                executed.append(k)
                keys.append(k)
        runs.append({"run": len(runs) + 1, "turns": [start, end], "events": events})
        state = CarriedState(case_id, end + 1, state.transcript_ref, f"summary through turn {end}",
                             tuple(keys[-50:]), None)
    return {"runs": runs, "effects_executed": len(executed), "unique_effects": len(set(executed)),
            "carried_state_example": asdict(state)}


def mid_turn_boundary(key_scheme: str, case_id: str = "CASE-7731"):
    """Continue-as-new cut in the middle of turn 200: the effect ran, the turn was not marked done.

    The next run starts again at turn 200. The tool keeps an idempotency store keyed by whatever key
    the workflow sends. A key built from the run id changes across the boundary; a key built from the
    case id and turn number does not.
    """
    store, sent = set(), 0
    for run_id, turns in (("run-a", [200]), ("run-b", [200, 201])):
        for n in turns:
            key = f"{run_id}:turn-{n}" if key_scheme == "run_id" else effect_key(case_id, n, "issue_refund")
            if key not in store:
                store.add(key)
                if n == 200:
                    sent += 1
    return {"key_scheme": key_scheme, "refunds_sent_for_turn_200": sent}


def main():
    t = Turn()
    out = {"events_per_turn": events_per_turn(t), "transcript_bytes_per_turn": transcript_growth(t),
           "inline_transcript": first_limit(t, True), "transcript_by_reference": first_limit(t, False),
           "chain_500_turns_every_200": chain(t, 500, 200),
           "mid_turn_boundary": [mid_turn_boundary("run_id"), mid_turn_boundary("case_turn")]}
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
