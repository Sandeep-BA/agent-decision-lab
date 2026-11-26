"""Author: Sandeep Belgavi. A connection pool that leaks CLOSE_WAIT sockets, and the fix.

A tiny keep-alive pool for a fictional Belgavi's Book Store stock service keeps idle sockets for reuse.
The stock service closes idle connections after a short time (it sends FIN). The buggy pool never
notices: it hands out a socket only when a request needs one, so idle sockets whose peer has closed
stay open on our side, which the operating system reports as CLOSE_WAIT. The fixed pool checks idle
sockets before reuse and on a sweep, and closes any whose peer has finished (a non-blocking peek
returns b'').

Everything runs on 127.0.0.1 with real sockets; no external service is contacted. probe.py shows the
same states through netstat on Windows.
"""
import json
import socket
import threading
import time


class StockServer:
    """Accepts connections, answers one request each, then closes idle ones after idle_close_s."""

    def __init__(self, idle_close_s: float = 0.2):
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(64)
        self.port = self.sock.getsockname()[1]
        self.idle_close_s = idle_close_s
        self._stop = False
        threading.Thread(target=self._serve, daemon=True).start()

    def _serve(self):
        self.sock.settimeout(0.05)
        while not self._stop:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                continue
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn):
        conn.settimeout(self.idle_close_s)
        try:
            while True:
                data = conn.recv(64)
                if not data:
                    break
                conn.sendall(b"in-stock\n")
        except socket.timeout:
            pass
        finally:
            conn.close()          # server closes idle connection: FIN to the client

    def stop(self):
        self._stop = True
        self.sock.close()


def peer_closed(s: socket.socket) -> bool:
    """True if the peer has sent FIN: a non-blocking peek returns b''."""
    s.setblocking(False)
    try:
        return s.recv(1, socket.MSG_PEEK) == b""
    except BlockingIOError:
        return False
    except OSError:
        return True
    finally:
        s.setblocking(True)


class Pool:
    def __init__(self, port: int, check_idle: bool):
        self.port, self.check_idle, self.idle = port, check_idle, []

    def request(self, sku: str) -> bytes:
        s = None
        while self.idle:
            cand = self.idle.pop()
            if self.check_idle and peer_closed(cand):
                cand.close()
                continue
            s = cand
            break
        if s is None:
            s = socket.create_connection(("127.0.0.1", self.port))
        s.sendall(sku.encode() + b"\n")
        reply = s.recv(64)
        self.idle.append(s)
        return reply

    def sweep(self) -> int:
        """Close idle sockets whose peer finished; returns how many were closed."""
        if not self.check_idle:
            return 0
        keep, closed = [], 0
        for s in self.idle:
            if peer_closed(s):
                s.close()
                closed += 1
            else:
                keep.append(s)
        self.idle = keep
        return closed

    def half_closed(self) -> int:
        return sum(1 for s in self.idle if peer_closed(s))

    def close(self):
        for s in self.idle:
            s.close()
        self.idle = []


def scenario(check_idle: bool, bursts: int = 5, per_burst: int = 4):
    server = StockServer()
    pool = Pool(server.port, check_idle)
    try:
        for b in range(bursts):
            # A burst opens several connections at once (no idle socket is free for each request).
            conns = [socket.create_connection(("127.0.0.1", server.port)) for _ in range(per_burst)]
            for i, s in enumerate(conns):
                s.sendall(f"BK-{b}{i}\n".encode())
                s.recv(64)
            pool.idle.extend(conns)
            time.sleep(0.35)          # longer than the server idle timeout
            pool.sweep()
        time.sleep(0.1)
        return {"check_idle": check_idle, "idle_sockets_held": len(pool.idle), "half_closed_held": pool.half_closed()}
    finally:
        pool.close()
        server.stop()


def main():
    out = [scenario(False), scenario(True)]
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
