"""Author: Sandeep Belgavi. Table tests for envsubst.py, plus a cross-check against sh when present."""
import shutil
import subprocess
import unittest
from envsubst import expand, MissingVariable

D = "https://default.example.test"


class ExpandTests(unittest.TestCase):
    def test_colon_dash_treats_empty_as_missing(self):
        self.assertEqual(expand("${API_BASE:-%s}" % D, {"API_BASE": ""}), D)

    def test_dash_keeps_empty(self):
        self.assertEqual(expand("${API_BASE-%s}" % D, {"API_BASE": ""}), "")

    def test_both_default_when_unset(self):
        self.assertEqual(expand("${API_BASE:-%s}" % D, {}), D)
        self.assertEqual(expand("${API_BASE-%s}" % D, {}), D)

    def test_ignore_colon_variant_is_the_reported_bug(self):
        self.assertEqual(expand("${API_BASE:-%s}" % D, {"API_BASE": ""}, colon_aware=False), "")

    def test_required_forms(self):
        with self.assertRaises(MissingVariable):
            expand("${TOKEN:?set TOKEN}", {"TOKEN": ""})
        self.assertEqual(expand("${TOKEN?set TOKEN}", {"TOKEN": ""}), "")

    def test_plus_forms(self):
        self.assertEqual(expand("${FLAG:+on}", {"FLAG": ""}), "")
        self.assertEqual(expand("${FLAG+on}", {"FLAG": ""}), "on")

    def test_python_idioms(self):
        env = {"API_BASE": ""}
        self.assertEqual(env.get("API_BASE", D), "")          # like ${API_BASE-D}
        self.assertEqual(env.get("API_BASE") or D, D)          # like ${API_BASE:-D}

    @unittest.skipUnless(shutil.which("sh"), "no POSIX sh on PATH")
    def test_matches_sh(self):
        for form in ("${V:-d}", "${V-d}", "${V:+r}", "${V+r}"):
            for env in ({}, {"V": ""}, {"V": "x"}):
                sh_env = {"PATH": __import__("os").environ["PATH"], **env}
                out = subprocess.run(["sh", "-c", f'printf %s "{form}"'], capture_output=True, text=True, env=sh_env).stdout
                self.assertEqual(out, expand(form, env), (form, env))


if __name__ == "__main__":
    unittest.main()
