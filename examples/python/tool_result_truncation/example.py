"""Cap large tool results with a truncation record the agent can see. Author: Sandeep Belgavi.

The adapter between a tool and the model enforces a byte budget on the serialized result.
It never cuts inside a JSON value: arrays are cut at whole items, text at a line boundary
(or a UTF-8 safe character boundary when one line exceeds the budget). Every truncated
result carries a record with returned/total counts and a continuation offset, so the model
can ask for the next page instead of treating a partial result as complete. Synthetic data.
"""
import json


def _size(obj):
    return len(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def cap_items(items, budget_bytes, offset=0):
    """Return a JSON-serializable envelope whose encoded size is <= budget_bytes."""
    if offset < 0 or offset > len(items):
        raise ValueError("offset outside result")
    envelope = {"items": [], "truncation": {"truncated": False, "returned": 0,
                                            "total": len(items), "offset": offset,
                                            "next_offset": None}}
    if _size(envelope) > budget_bytes:
        raise ValueError("budget smaller than an empty envelope")
    for i in range(offset, len(items)):
        envelope["items"].append(items[i])
        envelope["truncation"].update(returned=len(envelope["items"]))
        probe = dict(envelope, truncation=dict(envelope["truncation"], truncated=True, next_offset=i + 1))
        if _size(probe) > budget_bytes:
            envelope["items"].pop()
            envelope["truncation"].update(returned=len(envelope["items"]), truncated=True, next_offset=i)
            if not envelope["items"]:
                envelope["truncation"]["reason"] = "single item exceeds budget"
            return envelope
    return envelope


def cap_text(text, budget_bytes):
    """Cut text at the last newline that fits; fall back to a character boundary."""
    data = text.encode("utf-8")
    if len(data) <= budget_bytes:
        return {"text": text, "truncation": {"truncated": False, "returned_bytes": len(data), "total_bytes": len(data)}}
    head = data[:budget_bytes]
    cut = head.rfind(b"\n")
    if cut > 0:
        head = head[:cut + 1]
    else:
        while head and (head[-1] & 0xC0) == 0x80:  # drop UTF-8 continuation bytes
            head = head[:-1]
        if head and head[-1] >= 0xC0:  # drop a dangling lead byte
            head = head[:-1]
    return {"text": head.decode("utf-8"), "truncation": {"truncated": True, "returned_bytes": len(head),
                                                       "total_bytes": len(data), "next_byte_offset": len(head)}}


def naive_cut(items, budget_bytes):
    """What a byte slice of the serialized result produces: usually invalid JSON."""
    return json.dumps(items, ensure_ascii=False).encode("utf-8")[:budget_bytes].decode("utf-8", "ignore")


def fixture():
    return [{"order": f"BK-{1000 + i}", "title": f"Book {i}", "status": "returned" if i % 7 == 0 else "delivered",
             "note": "Customer Geetha asked about the refund" if i == 13 else ""} for i in range(40)]


def demo():
    items = fixture()
    first = cap_items(items, 900)
    second = cap_items(items, 900, first["truncation"]["next_offset"])
    try:
        json.loads(naive_cut(items, 900))
        naive_valid = True
    except json.JSONDecodeError:
        naive_valid = False
    pages, offset = 0, 0
    while offset is not None and offset < len(items):
        page = cap_items(items, 900, offset)
        pages += 1
        offset = page["truncation"]["next_offset"]
    return {"first_page": first["truncation"], "second_page": second["truncation"],
            "pages_to_read_all": pages, "naive_slice_is_valid_json": naive_valid,
            "text": cap_text("line one\nline two\nlíne three\n", 20)["truncation"]}


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
