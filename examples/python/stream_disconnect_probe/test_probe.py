# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

"""Offline check of the probe against a tiny stub streaming server that stops writing when the client leaves."""
import http.server
import json
import threading
import time
import unittest

import probe


class Stub(http.server.BaseHTTPRequestHandler):
    produced = []
    lock = threading.Lock()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(length))
        total = req["options"]["num_predict"]
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        sent = 0
        with Stub.lock:
            try:
                for i in range(total):
                    self.wfile.write((json.dumps({"response": "x", "done": False}) + "\n").encode())
                    self.wfile.flush()
                    sent += 1
                    time.sleep(0.002)
                self.wfile.write((json.dumps({"response": "", "done": True}) + "\n").encode())
                self.wfile.flush()
            except OSError:
                pass
            Stub.produced.append(sent)

    def log_message(self, *a):
        pass


class ProbeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stub)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_disconnect_frees_the_slot_sooner(self):
        probe.stream(5, port=self.port)
        control_a, control_b = probe.trial(False, num_predict=200, port=self.port)
        aborted_a, aborted_b = probe.trial(True, num_predict=200, port=self.port)
        self.assertFalse(control_a["aborted"])
        self.assertTrue(aborted_a["aborted"])
        self.assertLess(aborted_b["first"], control_b["first"])

    def test_stub_stopped_early_after_disconnect(self):
        Stub.produced.clear()
        probe.trial(True, num_predict=500, port=self.port)
        self.assertLess(min(Stub.produced), 500)


if __name__ == "__main__":
    unittest.main()
