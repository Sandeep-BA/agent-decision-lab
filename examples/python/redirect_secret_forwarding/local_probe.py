"""Author: Sandeep Belgavi. Local two-host redirect probe: a token endpoint on 127.0.0.1
redirects to a recorder on localhost (a different hostname, so a different origin).
The recorder reports which secrets arrived. Synthetic secrets; loopback only."""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

SECRETS = {"authorization": "Bearer at-SYNTHETIC-111", "x-api-key": "key-SYNTHETIC-222",
           "body": "grant_type=refresh_token&refresh_token=rt-SYNTHETIC-333&client_secret=cs-SYNTHETIC-444"}
RECORDED = []


class Recorder(BaseHTTPRequestHandler):
    def _record(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode() if n else ""
        RECORDED.append({"method": self.command, "authorization": "authorization" in {k.lower() for k in self.headers},
                         "x_api_key": "x-api-key" in {k.lower() for k in self.headers},
                         "refresh_token_in_body": "rt-SYNTHETIC-333" in body})
        self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"ok")
    do_GET = do_POST = _record

    def log_message(self, *a):
        pass


def make_origin(target_port, status):
    class Origin(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0); self.rfile.read(n)
            self.send_response(status); self.send_header("Location", f"http://localhost:{target_port}/collect")
            self.send_header("Content-Length", "0"); self.end_headers()

        def log_message(self, *a):
            pass
    return Origin


def serve(handler):
    s = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def run_requests(status):
    import requests
    rec = serve(Recorder)
    org = serve(make_origin(rec.server_port, status))
    RECORDED.clear()
    requests.post(f"http://127.0.0.1:{org.server_port}/token", data=SECRETS["body"],
                  headers={"Authorization": SECRETS["authorization"], "X-Api-Key": SECRETS["x-api-key"],
                           "Content-Type": "application/x-www-form-urlencoded"}, timeout=5)
    rec.shutdown(); org.shutdown()
    return dict(RECORDED[-1], status=status, client="requests " + requests.__version__)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        # For the Node probe: start recorder and a 307 origin and print their ports, then wait.
        status = int(sys.argv[2]) if len(sys.argv) > 2 else 307
        rec = serve(Recorder); org = serve(make_origin(rec.server_port, status))
        print(json.dumps({"origin": org.server_port}), flush=True)
        sys.stdin.readline()
        print(json.dumps(RECORDED[-1] if RECORDED else {}), flush=True)
    else:
        for st in (301, 302, 303, 307, 308):
            print(json.dumps(run_requests(st)))
