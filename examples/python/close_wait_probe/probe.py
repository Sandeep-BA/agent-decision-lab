"""Author: Sandeep Belgavi. Reproduce CLOSE_WAIT on loopback and read the states with netstat.

The server accepts N connections and closes each one immediately (it sends FIN).
The client keeps its sockets open without reading EOF or calling close(), so each
client-side socket stays in CLOSE_WAIT while the server side sits in FIN_WAIT_2.
"""
import os, socket, subprocess, sys, threading, time

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5


def states(port):
    out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True).stdout
    rows = [line.split() for line in out.splitlines() if f":{port}" in line]
    counts = {}
    for r in rows:
        if len(r) >= 4 and r[0] == "TCP":
            side = "server" if r[1].endswith(f":{port}") else "client"
            key = side + " " + r[3]
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


srv = socket.socket()
srv.bind(("127.0.0.1", 0))
srv.listen(16)
port = srv.getsockname()[1]


def serve():
    for _ in range(N):
        conn, _ = srv.accept()
        conn.close()  # server is the active closer: sends FIN


t = threading.Thread(target=serve, daemon=True)
t.start()
clients = [socket.create_connection(("127.0.0.1", port)) for _ in range(N)]
t.join(5)
time.sleep(0.5)
print("python", sys.version.split()[0], "platform", sys.platform, "pid", os.getpid())
print("after server close, client open:", states(port))
# A read now returns b'' (EOF): the peer has finished sending. The socket is still ours to close.
print("recv on first client returns", clients[0].recv(16))
time.sleep(0.2)
print("after reading EOF but not closing:", states(port))
for c in clients:
    c.close()
time.sleep(2)
print("after client close():", states(port))
srv.close()
