# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

import pathlib
import unittest

from plan_flip import plan_kind

HERE = pathlib.Path(__file__).parent


class PlanKindTest(unittest.TestCase):
    def test_generic_plan_has_a_parameter_placeholder(self):
        lines = (HERE / "fixtures" / "generic_plan.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(plan_kind(lines), "generic")

    def test_custom_plan_shows_the_literal(self):
        lines = (HERE / "fixtures" / "custom_plan.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(plan_kind(lines), "custom")


if __name__ == "__main__":
    unittest.main()
