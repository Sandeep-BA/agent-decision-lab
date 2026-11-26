"""Author: Sandeep Belgavi. Tests for half-closed socket detection in a keep-alive pool."""
import json
import socket
import time
import unittest
from pathlib import Path
from example import Pool, StockServer, peer_closed, scenario


class CloseWait(unittest.TestCase):
    def test_peer_close_is_visible_as_eof(self):
        server = StockServer(idle_close_s=0.05)
        try:
            s = socket.create_connection(("127.0.0.1", server.port))
            self.assertFalse(peer_closed(s))
            time.sleep(0.3)
            self.assertTrue(peer_closed(s))
            self.assertEqual(s.recv(16), b"")      # EOF, yet the socket is still ours to close
            s.close()
        finally:
            server.stop()

    def test_buggy_pool_keeps_half_closed_sockets(self):
        r = scenario(False, bursts=2, per_burst=3)
        self.assertEqual((r["idle_sockets_held"], r["half_closed_held"]), (6, 6))

    def test_fixed_pool_closes_them(self):
        r = scenario(True, bursts=2, per_burst=3)
        self.assertEqual((r["idle_sockets_held"], r["half_closed_held"]), (0, 0))

    def test_reuse_skips_a_dead_idle_socket(self):
        server = StockServer(idle_close_s=0.05)
        try:
            pool = Pool(server.port, check_idle=True)
            self.assertEqual(pool.request("BK-1"), b"in-stock\n")
            time.sleep(0.3)
            self.assertEqual(pool.request("BK-2"), b"in-stock\n")   # would fail on the dead socket
            pool.close()
        finally:
            server.stop()

    def test_buggy_pool_reuses_a_dead_socket(self):
        server = StockServer(idle_close_s=0.05)
        try:
            pool = Pool(server.port, check_idle=False)
            pool.request("BK-1")
            time.sleep(0.3)
            try:
                reply = pool.request("BK-2")
            except OSError:          # reset or abort, depending on the platform
                reply = None
            self.assertIn(reply, (None, b""))
            pool.close()
        finally:
            server.stop()

    def test_expected_file_shape(self):
        expected = json.loads(Path(__file__).with_name("expected.json").read_text(encoding="utf-8"))
        self.assertEqual(expected[0]["half_closed_held"], 20)
        self.assertEqual(expected[1]["half_closed_held"], 0)


if __name__ == "__main__":
    unittest.main()
