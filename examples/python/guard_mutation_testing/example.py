"""Mutation-test the deterministic guard around an agent's refund proposal. Author: Sandeep Belgavi.

The guard decides whether a refund proposed by an agent may run automatically, needs a
human approval, or is rejected. Small mutants of the guard are generated with the ast
module; a test suite "kills" a mutant if at least one of its cases now fails. Surviving
mutants show which guard behaviours the suite never pins. Synthetic data only.
"""
import ast
import copy
import json

GUARD_SOURCE = '''
def refund_guard(p):
    if p["case_state"] != "verified":
        return "reject"
    if p["currency"] != p["order_currency"]:
        return "reject"
    if p["amount_cents"] <= 0 or p["amount_cents"] > p["order_total_cents"]:
        return "reject"
    if p["amount_cents"] > 5000 or p["prior_refunds"] >= 1:
        return "approve_first"
    return "auto"
'''

BASE = {"case_state": "verified", "currency": "INR", "order_currency": "INR",
        "amount_cents": 1200, "order_total_cents": 3000, "prior_refunds": 0}


def case(expected, **changes):
    return (dict(BASE, **changes), expected)


# A suite written from the happy path plus one obvious rejection.
WEAK_SUITE = [
    case("auto"),
    case("reject", case_state="awaiting_verification"),
    case("approve_first", amount_cents=2900, order_total_cents=9000, prior_refunds=1),
]

# The same suite with boundary and each-clause cases added.
STRONG_SUITE = WEAK_SUITE + [
    case("reject", currency="USD"),
    case("reject", amount_cents=0),
    case("auto", amount_cents=1),
    case("reject", amount_cents=3001),
    case("auto", amount_cents=3000),
    case("auto", amount_cents=5000, order_total_cents=9000),
    case("approve_first", amount_cents=5001, order_total_cents=9000),
    case("approve_first", prior_refunds=1),
]

SWAPS = {ast.Lt: [ast.LtE, ast.Gt], ast.LtE: [ast.Lt, ast.GtE], ast.Gt: [ast.GtE, ast.Lt],
         ast.GtE: [ast.Gt, ast.LtE], ast.Eq: [ast.NotEq], ast.NotEq: [ast.Eq]}


def mutants(source=GUARD_SOURCE):
    """Yield (description, mutated_source). Operators, constants, boolean ops, clause removal."""
    tree = ast.parse(source)
    nodes = list(ast.walk(tree))
    for i, node in enumerate(nodes):
        if isinstance(node, ast.Compare):
            for new in SWAPS.get(type(node.ops[0]), []):
                yield _mutate(tree, i, lambda n, new=new: setattr(n, "ops", [new()]),
                              f"line {node.lineno}: {type(node.ops[0]).__name__} -> {new.__name__}")
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
            for delta in (1, -1):
                yield _mutate(tree, i, lambda n, d=delta: setattr(n, "value", n.value + d),
                              f"line {node.lineno}: constant {node.value} -> {node.value + delta}")
        if isinstance(node, ast.BoolOp):
            other = ast.Or if isinstance(node.op, ast.And) else ast.And
            yield _mutate(tree, i, lambda n, o=other: setattr(n, "op", o()),
                          f"line {node.lineno}: {type(node.op).__name__} -> {other.__name__}")
            for k in range(len(node.values)):
                yield _mutate(tree, i, lambda n, k=k: n.values.pop(k),
                              f"line {node.lineno}: drop operand {k + 1} of {type(node.op).__name__}")
        if isinstance(node, ast.If):
            yield _mutate(tree, i, lambda n: setattr(n, "test", ast.Constant(False)),
                          f"line {node.lineno}: if-branch never taken")


def _mutate(tree, index, change, label):
    clone = copy.deepcopy(tree)
    target = list(ast.walk(clone))[index]
    change(target)
    return label, ast.unparse(ast.fix_missing_locations(clone))


def load(source):
    scope = {}
    exec(compile(source, "<guard>", "exec"), scope)
    return scope["refund_guard"]


def run_suite(guard, suite):
    return [i for i, (proposal, expected) in enumerate(suite) if guard(proposal) != expected]


def score(suite):
    assert run_suite(load(GUARD_SOURCE), suite) == [], "suite must pass on the real guard"
    killed, survived, equivalent_candidates = [], [], []
    for label, src in mutants():
        failures = run_suite(load(src), suite)
        (killed if failures else survived).append(label)
    return {"mutants": len(killed) + len(survived), "killed": len(killed),
            "survived": len(survived), "survivors": survived}


def demo():
    return {"weak": score(WEAK_SUITE), "strong": score(STRONG_SUITE)}


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
