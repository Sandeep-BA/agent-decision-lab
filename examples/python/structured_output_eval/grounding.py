"""Checks a schema cannot express: is each extracted value actually in the message? Author: Sandeep Belgavi."""
import re


def _digits(text):
    return re.sub(r'[^0-9]', '', text)


def ungrounded(obj, text):
    """Field names whose value does not appear in the source text. Null is always grounded."""
    bad = []
    oid = obj.get('order_id')
    if oid is not None:
        found = {'BK-' + m for m in re.findall(r'\bbk[\s-]?([0-9]{5})\b', text, re.I)}
        if oid not in found:
            bad.append('order_id')
    amount = obj.get('amount_inr')
    if amount is not None:
        numbers = {int(_digits(n)) for n in re.findall(r'[0-9][0-9,]*', text) if _digits(n)}
        if not (isinstance(amount, (int, float)) and float(amount).is_integer() and int(amount) in numbers):
            bad.append('amount_inr')
    return bad
