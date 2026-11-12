"""Author: Sandeep Belgavi. Print the shrunk counterexample Hypothesis reports for check_buggy."""
from hypothesis import given, settings, strategies as st
from test_guard_properties import proposals, run, SETTINGS


@SETTINGS
@given(st.integers(1, 1_500_000), proposals)
def cumulative(total, plan):
    _, decisions = run(__import__("guard").check_buggy, total, "delivered", plan)
    assert sum(a for a, d in decisions if d == "accept") <= total, decisions


try:
    cumulative()
except AssertionError as e:
    print("Falsified:", e)
    for note in getattr(e, "__notes__", []):
        print(note)
