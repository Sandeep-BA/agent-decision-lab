"""Author: Sandeep Belgavi. Tests for the offline simulated-user evaluation example (no model calls)."""
import random
import unittest

import simeval as s


class SimulatedUserEvalTests(unittest.TestCase):
    def setUp(self):
        self.tasks = s.load_tasks()

    def test_patient_persona_hides_the_policy_bug(self):
        r = s.run(self.tasks, "waits", careful=False)
        self.assertEqual((r["pass^1"], r["pass^k"]), (1.0, 1.0))

    def test_detailed_persona_exposes_it_on_the_late_order(self):
        r = s.run(self.tasks, "detailed", careful=False)
        self.assertEqual(r["successes_per_task"], [4, 0, 4, 4])
        self.assertEqual(r["failures"], {"agent": 4, "simulator": 0})

    def test_pass_k_punishes_inconsistency(self):
        r = s.run(self.tasks, "mixed", careful=False)
        self.assertEqual((r["pass^1"], r["pass^k"]), (0.938, 0.75))

    def test_careful_agent_passes_every_persona(self):
        for persona in ("waits", "detailed", "mixed"):
            self.assertEqual(s.run(self.tasks, persona, careful=True)["pass^1"], 1.0)

    def test_simulator_drift_is_attributed_to_the_simulator(self):
        r = s.run(self.tasks, "detailed", careful=True, drift=0.25)
        self.assertEqual((r["pass^1"], r["pass^k"]), (0.875, 0.75))
        self.assertEqual(r["failures"], {"agent": 0, "simulator": 2})

    def test_turn_limit_stops_a_conversation(self):
        task = {"facts": {}, "expected_change": None}
        user = s.SimUser(task, "waits", random.Random(1), 0.0)
        self.assertEqual(s.agent_turns(user, user.first_message(), True)["outcome"], "stopped: turn limit")


if __name__ == "__main__":
    unittest.main()
