"""Tests for the host-owned runtime model. Author: Sandeep Belgavi."""
import unittest
from host_runtime import HostAdmission, call_tool, cold_resume, start_thread, submit


class HostRuntimeTest(unittest.TestCase):
    def test_restricted_thread_loses_root_only_tools(self):
        t = start_thread("thr-1", restrict_root_capabilities=True)
        self.assertEqual(t.tools(), ["draft_reply", "read_case"])
        self.assertTrue(call_tool(t, "ask_user").startswith("refused"))
        self.assertEqual(call_tool(t, "read_case"), "ok: read_case")

    def test_unrestricted_thread_keeps_them(self):
        self.assertIn("ask_user", start_thread("thr-1").tools())

    def test_denied_admission_keeps_input(self):
        host = HostAdmission(1)
        held = host.acquire("other")
        t = start_thread("thr-1")
        self.assertEqual(submit(t, host, "first"), "denied")
        self.assertEqual(t.pending_input, ["first"])
        held.release()
        self.assertEqual(submit(t, host, "second"), "ran")
        users = [m for r, m in t.transcript if r == "user"]
        self.assertEqual(users, ["first", "second"])
        self.assertEqual(host.in_use, 0)

    def test_guard_released_even_if_turn_fails(self):
        host = HostAdmission(1)
        t = start_thread("thr-1")
        t.tools = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
        with self.assertRaises(RuntimeError):
            submit(t, host, "x")
        self.assertEqual(host.in_use, 0)

    def test_cold_resume_needs_the_marker_again(self):
        t = start_thread("thr-1", restrict_root_capabilities=True)
        saved = {"thread_id": t.thread_id, "session_id": t.session_id, "transcript": []}
        self.assertIn("install_plugin", cold_resume(saved).tools())
        self.assertNotIn("install_plugin", cold_resume(saved, True).tools())

    def test_inherited_session_id_rules(self):
        child = start_thread("thr-2", inherited_session_id="sess-1")
        self.assertEqual((child.thread_id, child.session_id), ("thr-2", "sess-1"))
        for kind in ("resumed", "forked", "native_child"):
            with self.assertRaises(ValueError):
                start_thread("thr-2", kind=kind, inherited_session_id="sess-1")
        with self.assertRaises(ValueError):
            start_thread("thr-2", inherited_session_id="thr-2")


if __name__ == "__main__":
    unittest.main()
