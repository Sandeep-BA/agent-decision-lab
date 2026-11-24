# Author: Sandeep Belgavi. Original single-range response consumer.
def strong(tag):
    return isinstance(tag, str) and tag.startswith('"') and tag.endswith('"')

def consume(prefix, saved_tag, status, body, response_tag, content_range=None):
    if not isinstance(prefix, bytes) or not isinstance(body, bytes):
        raise ValueError("byte inputs required")
    if status == 200:
        return {"action": "replace", "bytes": body, "tag": response_tag}
    if status != 206:
        raise ValueError("response needs separate recovery")
    if not strong(saved_tag) or response_tag != saved_tag:
        raise ValueError("partial representation identity mismatch")
    if not isinstance(content_range, tuple) or len(content_range) != 3:
        raise ValueError("missing parsed Content-Range")
    start, end, total = content_range
    if any(type(v) is not int for v in content_range):
        raise ValueError("integer range bounds required")
    if start != len(prefix) or end < start or end + 1 != total:
        raise ValueError("range is not the requested remaining suffix")
    if len(body) != end - start + 1:
        raise ValueError("truncated range body")
    return {"action": "append", "bytes": prefix + body, "tag": response_tag}

assert consume(b"ABCD", '"v1"', 206, b"EFGH", '"v1"', (4, 7, 8))["bytes"] == b"ABCDEFGH"
assert consume(b"ABCD", '"v1"', 200, b"12345678", '"v2"')["bytes"] == b"12345678"


def run_demo(fixture):
    r = consume(fixture["prefix"].encode(), fixture["saved_tag"], fixture["status"], fixture["body"].encode(), fixture["response_tag"], tuple(fixture["range"]))
    return {"action":r["action"],"bytes":r["bytes"].decode(),"tag":r["tag"]}

if __name__ == "__main__":
    import json
    from pathlib import Path
    fixture = json.loads(Path(__file__).with_name("sample-input.json").read_text(encoding="utf-8"))
    print(json.dumps(run_demo(fixture),sort_keys=True))
