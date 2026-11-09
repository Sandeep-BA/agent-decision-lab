# Author: Sandeep Belgavi. Offline request-shape example.
from copy import deepcopy

def request_plan(history, pending, previous_id, system, tools):
    if previous_id:
        return {
            "messages": deepcopy(pending),
            "thread": {"type": "continue", "previous_message_id": previous_id},
        }
    return {
        "messages": deepcopy(history + pending),
        "system": system,
        "tools": deepcopy(tools),
        "thread": {"type": "create"},
    }


def recovery_for(status=None, error_code=None, stop_reason=None):
    """Next step for a documented outcome. A pure table: it makes no call."""
    if stop_reason == "refusal":
        return "new_thread_without_refused_turn"
    table = {
        (404, "thread_not_found"): "replay_full_conversation",
        (400, "thread_already_continued"): "continue_latest_or_replay_if_response_lost",
        (400, "thread_continue_in_flight"): "wait_then_continue_or_replay",
        (400, "thread_fingerprint_mismatch"): "fix_field_or_start_new_thread",
        (400, "thread_unsupported_request"): "remove_feature_or_send_without_thread",
    }
    if status is None:
        return "continue_normally"
    return table.get((status, error_code), "surface_error")
