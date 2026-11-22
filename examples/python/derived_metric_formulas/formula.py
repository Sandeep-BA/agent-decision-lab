# Author: Sandeep Belgavi. An original Python model of the derived-metric formula rules that
# promptfoo 0.126.0 documents and enforces (numeric literals, score names, + - * /, unary +/-,
# comparisons without chains, condition ? a : b, at most 1,024 characters). It is not promptfoo
# code and does not run promptfoo. Synthetic score rows; standard library only.
"""Run: python formula.py"""
import json
import math
import re

MAX_LEN = 1024
TOKEN = re.compile(r'\s*(?:(?P<num>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)|(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)'
                   r'|(?P<op>\*\*|>=|<=|==|!=|[-+*/()<>?:,.=;]))')
COMPARE = {'>', '>=', '<', '<=', '==', '!='}


LEFTOVER = {'=': 'assignments are not allowed', '.': 'property access is not allowed',
            '**': 'operator ** is not allowed', ',': 'expected a single expression', ';': 'expected a single expression'}


class FormulaError(ValueError):
    pass


def tokenize(src):
    pos, out = 0, []
    while pos < len(src):
        if src[pos:].strip() == '':
            break
        m = TOKEN.match(src, pos)
        if not m or m.end() == pos:
            raise FormulaError(f'unsupported syntax at character {pos}: {src[pos:pos + 12]!r}')
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
        pos = m.end()
    return out


def js_div(a, b):
    if b == 0:
        if a == 0 or math.isnan(a):
            return math.nan
        return math.copysign(math.inf, a) * math.copysign(1.0, b)
    return a / b


BINARY = {'+': lambda a, b: a + b, '-': lambda a, b: a - b, '*': lambda a, b: a * b, '/': js_div,
          '>': lambda a, b: float(a > b), '>=': lambda a, b: float(a >= b), '<': lambda a, b: float(a < b),
          '<=': lambda a, b: float(a <= b), '==': lambda a, b: float(a == b), '!=': lambda a, b: float(a != b)}


class Parser:
    def __init__(self, tokens):
        self.t, self.i = tokens, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, value=None):
        tok = self.peek()
        if tok[0] is None or (value is not None and tok[1] != value):
            raise FormulaError(f'expected {value or "a value"}')
        self.i += 1
        return tok

    def expression(self):  # conditional, lowest precedence, right-associative
        test = self.binary(0)
        if self.peek()[1] == '?':
            self.take('?'); yes = self.expression(); self.take(':'); no = self.expression()
            return ('cond', test, yes, no, False)
        return test

    LEVELS = [('==', '!='), ('<', '<=', '>', '>='), ('+', '-'), ('*', '/')]

    def binary(self, level):
        if level == len(self.LEVELS):
            return self.unary()
        left = self.binary(level + 1)
        while self.peek()[0] == 'op' and self.peek()[1] in self.LEVELS[level]:
            op = self.take()[1]
            right = self.binary(level + 1)
            if op in COMPARE and any(n[0] == 'bin' and n[1] in COMPARE and not n[-1] for n in (left, right)):
                raise FormulaError('use separate comparisons in a conditional instead of a comparison chain')
            left = ('bin', op, left, right, False)
        return left

    def unary(self):
        if self.peek()[1] in ('+', '-'):
            op = self.take()[1]
            node = self.unary()
            return ('neg', node, False) if op == '-' else node
        return self.primary()

    def primary(self):
        kind, value = self.take()
        if kind == 'num':
            v = float(value)
            if not math.isfinite(v):
                raise FormulaError('numeric literal must be finite')
            return ('num', v, False)
        if kind == 'name':
            if self.peek()[1] == '(':
                raise FormulaError(f'function calls are not allowed: {value}(...)')
            return ('name', value, False)
        if value == '(':
            node = self.expression(); self.take(')')
            return node[:-1] + (True,)  # mark as parenthesized
        raise FormulaError(f'unexpected {value!r}')


def compile_formula(name, formula):
    """Validate once, before any row is scored. Returns (evaluate, referenced_names)."""
    try:
        if len(formula) > MAX_LEN:
            raise FormulaError(f'formula exceeds {MAX_LEN} characters')
        p = Parser(tokenize(formula.strip()))
        tree = p.expression()
        if p.i != len(p.t):
            raise FormulaError(LEFTOVER.get(p.t[p.i][1], 'expected a single expression'))
    except FormulaError as e:
        raise FormulaError(f'Invalid formula for derived metric "{name}": {e}') from None
    names = set()

    def walk(n):
        if n[0] == 'name':
            names.add(n[1])
        for c in n[1:]:
            if isinstance(c, tuple):
                walk(c)
    walk(tree)

    def ev(n, s):
        k = n[0]
        if k == 'num':
            return n[1]
        if k == 'name':
            v = s.get(n[1])
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                raise KeyError(f'Missing numeric score: {n[1]}')
            return float(v)
        if k == 'neg':
            return -ev(n[1], s)
        if k == 'bin':
            return BINARY[n[1]](ev(n[2], s), ev(n[3], s))
        return ev(n[2], s) if ev(n[1], s) else ev(n[3], s)
    return (lambda scores: ev(tree, scores)), names


def score_rows(metrics, rows, known=None):
    """Compile every formula first, then evaluate per row; a missing score keeps the last value
    (0 initially) and is recorded, mirroring a debug log. known: optional set of score names."""
    compiled = {}
    for name, formula in metrics.items():
        fn, names = compile_formula(name, formula)
        if known is not None and not names <= known | set(metrics) | {'__count'}:
            raise FormulaError(f'derived metric "{name}" uses unknown scores: {sorted(names - known - set(metrics) - {"__count"})}')
        compiled[name] = fn
    values, logged = {n: 0.0 for n in metrics}, []
    totals = {}
    for count, row in enumerate(rows, 1):
        for k, v in row.items():
            totals[k] = totals.get(k, 0.0) + v
        ctx = dict(totals, __count=count)
        for name, fn in compiled.items():
            try:
                values[name] = fn(ctx)
                ctx[name] = values[name]
            except KeyError as e:
                logged.append(f'row {count}: could not evaluate {name}: {e.args[0]}')
    return values, logged


ROWS = [{'tp': 1, 'fp': 0, 'fn': 0}, {'tp': 0, 'fp': 1, 'fn': 0}, {'tp': 1, 'fp': 0, 'fn': 1}, {'tp': 1, 'fp': 0, 'fn': 0}]
F1 = 'tp + fp == 0 ? 0 : (tp + fn == 0 ? 0 : 2 * tp / (2 * tp + fp + fn))'


def run():
    out = {}
    out['f1'] = score_rows({'f1': F1}, ROWS)[0]['f1']
    out['zero_rows_f1'] = score_rows({'f1': F1}, [{'tp': 0, 'fp': 0, 'fn': 0}])[0]['f1']
    out['unguarded_zero_division'] = repr(score_rows({'precision': 'tp / (tp + fp)'}, [{'tp': 0, 'fp': 0, 'fn': 0}])[0]['precision'])
    rejected = {}
    for f in ['max(tp, fp)', 'tp.constructor', 'tp = 1', '0 < tp < 1', 'x' * 1025, 'tp ** 2', 'tp; fp']:
        try:
            compile_formula('m', f)
            rejected[f[:20]] = 'accepted'
        except FormulaError as e:
            rejected[f[:20]] = str(e).split(': ', 1)[1]
    out['rejected'] = rejected
    v, log = score_rows({'recall': 'tp / (tp + fnn)'}, ROWS)
    out['typo_without_name_check'] = {'value': v['recall'], 'debug_lines': len(log), 'first': log[0]}
    try:
        score_rows({'recall': 'tp / (tp + fnn)'}, ROWS, known={'tp', 'fp', 'fn'})
        out['typo_with_name_check'] = 'accepted'
    except FormulaError as e:
        out['typo_with_name_check'] = str(e)
    out['range_check'] = score_rows({'in_range': 'tp > 0 ? (tp < 5 ? 1 : 0) : 0'}, ROWS)[0]['in_range']
    return out


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
