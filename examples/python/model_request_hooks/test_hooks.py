"""Tests for the observation-only hook handler and the metrics aggregator. Author: Sandeep Belgavi."""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hook_observer  # noqa: E402
import metrics  # noqa: E402

PRE = json.loads((HERE / "fixtures" / "pre.json").read_text(encoding="utf-8"))
POST = json.loads((HERE / "fixtures" / "post.json").read_text(encoding="utf-8"))


class HandlerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pre_event_writes_only_a_marker(self):
        self.assertIsNone(hook_observer.handle(PRE, now=100.0, directory=self.dir))
        self.assertTrue((self.dir / "t-7.start").exists())
        self.assertFalse((self.dir / "requests.jsonl").exists())

    def test_post_event_records_one_attempt_with_latency(self):
        hook_observer.handle(PRE, now=100.0, directory=self.dir)
        record = hook_observer.handle(POST, now=101.25, directory=self.dir)
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["model"], "example-model-1")
        self.assertEqual(record["agent_type"], "root")
        self.assertEqual((record["input_tokens"], record["output_tokens"]), (1200, 85))
        self.assertEqual(record["latency_s"], 1.25)
        lines = (self.dir / "requests.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertFalse((self.dir / "t-7.start").exists(), "the marker is consumed")

    def test_null_usage_is_unknown_not_zero(self):
        cancelled = dict(POST, status="cancelled", token_usage=None, agent_type="explorer")
        record = hook_observer.handle(cancelled, now=5.0, directory=self.dir)
        self.assertIsNone(record["input_tokens"])
        self.assertIsNone(record["latency_s"], "no pre marker, so latency is unknown")
        self.assertEqual(record["agent_type"], "explorer")

    def test_stdout_stays_empty_even_for_a_record(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            hook_observer.handle(PRE, now=1.0, directory=self.dir)
            hook_observer.handle(POST, now=2.0, directory=self.dir)
        self.assertEqual(buf.getvalue(), "")

    def test_cli_rejects_invalid_json_with_exit_1_and_empty_stdout(self):
        proc = subprocess.run([sys.executable, str(HERE / "hook_observer.py")], input="not json",
                              capture_output=True, text=True, env={"HOOK_STATE_DIR": self.tmp.name, "PATH": ""})
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertIn("invalid JSON", proc.stderr)


class MetricsTests(unittest.TestCase):
    def test_attempts_are_counted_separately_from_turns(self):
        records = [
            {"turn": "t-1", "model": "m", "status": "failed", "input_tokens": 900, "output_tokens": 0, "latency_s": 2.0, "error": "context length"},
            {"turn": "t-1", "model": "m", "status": "completed", "input_tokens": 400, "output_tokens": 50, "latency_s": 1.0, "error": None},
            {"turn": "t-2", "model": "m", "status": "cancelled", "input_tokens": None, "output_tokens": None, "latency_s": None, "error": None},
        ]
        s = metrics.aggregate(records)
        self.assertEqual((s["turns"], s["attempts"]), (2, 3))
        self.assertAlmostEqual(s["attempts_per_turn"], 1.5)
        m = s["models"]["m"]
        self.assertEqual((m["completed"], m["failed"], m["cancelled"]), (1, 1, 1))
        self.assertEqual(m["input_tokens"], 1300)
        self.assertEqual(m["unknown_usage"], 1)
        text = metrics.render(s)
        self.assertIn("attempts_per_turn=1.50", text)
        self.assertIn("unknown_usage=1", text)


if __name__ == "__main__":
    unittest.main()
