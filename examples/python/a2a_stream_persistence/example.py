"""Author: Sandeep Belgavi. What a client persists and displays from a streamed A2A answer.

A remote specialist agent for the fictional Belgavi's Book Store streams its answer as
TaskArtifactUpdateEvent chunks (append, last_chunk) and closes the task with a status update. Three
client behaviours are compared:

  per_update   each artifact update becomes an event carrying only that update's parts, partial is
               'not last_chunk' (the assignment in ADK Python v2.15.1's RemoteA2aAgent)
  aggregate    partial events pass through, and a final non-partial event carrying the aggregated
               text is added when the artifact closes or the task reaches a terminal state (the idea
               of the 2.15.0 change that 2.15.1 reverted)
  recommended  same persisted record as aggregate, but the final event is marked as replacing the
               partial events for that artifact, so a display keyed by artifact id shows it once

Two displays read the events: 'append' concatenates every event; 'keyed' keeps one text per artifact
id and adds to it or replaces it according to each event's append flag. Persistence keeps only non-partial events (ADK does not persist
partial events). This is a model of the event flow, not ADK or an A2A SDK.
"""
import json

TERMINAL = {"completed", "failed", "canceled", "rejected", "input-required"}


def stream(kind: str):
    chunks = ["Your order ", "BK-2231 ", "ships Friday."]
    ev = []
    for i, c in enumerate(chunks):
        last = (i == len(chunks) - 1) and kind == "last_chunk_on_final_delta"
        ev.append({"type": "artifact", "artifact_id": "answer", "text": c, "append": i > 0, "last_chunk": last})
    if kind == "full_artifact_at_end":
        ev.append({"type": "artifact", "artifact_id": "answer", "text": "".join(chunks), "append": False, "last_chunk": True})
    ev.append({"type": "status", "state": "completed"})
    return ev


def client_events(events, policy: str):
    """Events the client emits. 'append' tells a display whether to add to or replace the artifact text."""
    out, buf, closed = [], {}, set()
    for e in events:
        if e["type"] == "artifact":
            aid = e["artifact_id"]
            buf[aid] = (buf.get(aid, "") + e["text"]) if e["append"] else e["text"]
            if policy == "per_update":
                out.append({"artifact_id": aid, "text": e["text"], "partial": not e["last_chunk"], "append": e["append"]})
                continue
            out.append({"artifact_id": aid, "text": e["text"], "partial": True, "append": e["append"]})
            if e["last_chunk"]:
                closed.add(aid)
                out.append(final_event(aid, buf[aid], policy))
        elif e["type"] == "status" and e["state"] in TERMINAL and policy != "per_update":
            for aid, text in buf.items():
                if aid not in closed:
                    out.append(final_event(aid, text, policy))
    return out


def final_event(aid, text, policy):
    # aggregate: a new event whose content is the whole answer, with nothing saying it repeats the partials.
    # recommended: the same content, explicitly marked as replacing what the partials showed.
    return {"artifact_id": aid, "text": text, "partial": False, "append": policy != "recommended"}


def persisted(evts):
    return "".join(e["text"] for e in evts if not e["partial"])


def display(evts, mode: str):
    if mode == "append":
        return "".join(e["text"] for e in evts)
    shown = {}
    for e in evts:
        aid = e["artifact_id"]
        shown[aid] = shown.get(aid, "") + e["text"] if e["append"] else e["text"]
    return "".join(shown.values())


def main():
    answer = "Your order BK-2231 ships Friday."
    out = {}
    for kind in ("deltas_then_status", "last_chunk_on_final_delta", "full_artifact_at_end"):
        out[kind] = {}
        for policy in ("per_update", "aggregate", "recommended"):
            ev = client_events(stream(kind), policy)
            out[kind][policy] = {"persisted": persisted(ev), "persisted_complete": persisted(ev) == answer,
                                 "append_display": display(ev, "append"),
                                 "append_display_duplicates": display(ev, "append") != answer,
                                 "keyed_display": display(ev, "keyed")}
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
