# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

"""Does a model server stop generating when a streaming client disconnects?

Compares how long request B waits behind request A, with A running to completion and with A's client hanging up early.
Point it at a real Ollama with one parallel slot to measure, or run the offline test against the stub server.
"""
import http.client
import json
import os
import socket
import statistics
import sys
import threading
import time

HOST = os.environ.get("MODEL_HOST", "127.0.0.1")
PORT = int(os.environ.get("MODEL_PORT", "11434"))
MODEL = os.environ.get("MODEL_NAME", "qwen2.5:0.5b-instruct")


def stream(num_predict, abort_after=None, host=HOST, port=PORT, on_first=None):
    start = time.perf_counter()
    conn = http.client.HTTPConnection(host, port, timeout=300)
    body = json.dumps({"model": MODEL, "prompt": "Write a long history of bookselling.", "stream": True,
                       "options": {"num_predict": num_predict, "temperature": 0, "seed": 7}})
    conn.request("POST", "/api/generate", body, {"Content-Type": "application/json"})
    resp = conn.getresponse()
    first = None
    chunks = 0
    for line in resp:
        if not line.strip():
            continue
        if first is None:
            first = time.perf_counter() - start
            if on_first:
                on_first()
        chunks += 1
        if abort_after and chunks >= abort_after:
            # http.client hands the socket to the response when the server closes after the body.
            sock = conn.sock or getattr(resp.fp, "raw", None) and resp.fp.raw._sock
            if sock:
                sock.shutdown(socket.SHUT_RDWR)
            resp.close()
            conn.close()
            return {"first": first, "chunks": chunks, "aborted": True, "end": time.perf_counter() - start}
    conn.close()
    return {"first": first, "chunks": chunks, "aborted": False, "end": time.perf_counter() - start}


def trial(abort, num_predict=600, **kw):
    first_seen = threading.Event()
    a = {}
    ta = threading.Thread(target=lambda: a.update(stream(num_predict, abort_after=30 if abort else None, on_first=first_seen.set, **kw)))
    ta.start()
    first_seen.wait(120)
    b = stream(20, **kw)
    ta.join()
    return a, b


if __name__ == "__main__":
    stream(5)  # warm the model
    for label, abort in (("control", False), ("disconnect", True)):
        waits = []
        for _ in range(3):
            _, b = trial(abort)
            waits.append(b["first"])
        print(label, "median B first-chunk wait", round(statistics.median(waits), 3), "s")
