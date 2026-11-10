"""Compare an old and a new LLM judge on a human-labelled anchor set.

Author: Sandeep Belgavi. Labels are binary pass (1) / fail (0). No judge model is called here;
the inputs are labels you already collected.
"""
from fractions import Fraction


def _check(*columns):
    n = len(columns[0])
    if n == 0 or any(len(c) != n for c in columns):
        raise ValueError('label columns must be non-empty and the same length')
    for c in columns:
        if any(v not in (0, 1) for v in c):
            raise ValueError('labels must be 0 or 1')
    return n


def cohen_kappa(a, b):
    """Exact Cohen's kappa for two binary raters; None when chance agreement is 1."""
    n = _check(a, b)
    po = Fraction(sum(x == y for x, y in zip(a, b)), n)
    pa, pb = Fraction(sum(a), n), Fraction(sum(b), n)
    pe = pa * pb + (1 - pa) * (1 - pb)
    if pe == 1:
        return None
    return (po - pe) / (1 - pe)


def compare(human, old, new, kappa_drop=Fraction(5, 100), max_flip=Fraction(10, 100)):
    """Return metrics and a decision about whether old scores can still be compared to new ones."""
    n = _check(human, old, new)
    flips_to_pass = sum(o == 0 and w == 1 for o, w in zip(old, new))
    flips_to_fail = sum(o == 1 and w == 0 for o, w in zip(old, new))
    k_old, k_new = cohen_kappa(human, old), cohen_kappa(human, new)
    flip_rate = Fraction(flips_to_pass + flips_to_fail, n)
    result = {
        'n': n,
        'kappa_old_vs_human': k_old,
        'kappa_new_vs_human': k_new,
        'kappa_old_vs_new': cohen_kappa(old, new),
        'pass_rate_old': Fraction(sum(old), n),
        'pass_rate_new': Fraction(sum(new), n),
        'flips_to_pass': flips_to_pass,
        'flips_to_fail': flips_to_fail,
        'flip_rate': flip_rate,
    }
    if k_new is None or k_old is None:
        result['decision'] = 'undefined: anchor labels have no variation'
    elif k_new < k_old - kappa_drop:
        result['decision'] = 'reject new judge: agrees less with people'
    elif flip_rate > max_flip or flips_to_pass != flips_to_fail:
        result['decision'] = 'adopt only with a re-baseline: rescore the baseline with the new judge'
    else:
        result['decision'] = 'adopt: old and new scores stay comparable on this anchor set'
    return result


def fixture():
    """Twenty synthetic help-desk answers for Belgavi's Book Store, labelled by Geetha."""
    human = [1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1]
    old = [1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1]
    new = [1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1]
    return human, old, new
