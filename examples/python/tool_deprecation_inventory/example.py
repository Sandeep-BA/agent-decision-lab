"""Retire a tool that agents still call: signals, a caller inventory and a removal gate.
Author: Sandeep Belgavi.

Formats the Deprecation (RFC 9745) and Sunset (RFC 8594) response fields, checks that the sunset is not
earlier than the deprecation, translates calls to the deprecated tool through a deterministic alias, and
groups the gateway log by caller and prompt version so the owner knows who must move before removal.
Synthetic gateway log for the fictional Belgavi's Book Store. Standard library only; no model is called.
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import json, sys

PLAN = {'tool': 'lookup_order_v1', 'replacement': 'lookup_order',
        'deprecated_at': datetime(2026, 12, 1, tzinfo=timezone.utc),
        'sunset_at': datetime(2027, 1, 15, tzinfo=timezone.utc),
        'doc': 'https://docs.bookstore.test/tools/lookup-order-migration'}


def headers(plan):
    if plan['sunset_at'] < plan['deprecated_at']:
        raise ValueError('Sunset must not be earlier than Deprecation (RFC 9745, section 4)')
    return {'Deprecation': f"@{int(plan['deprecated_at'].timestamp())}",
            'Sunset': format_datetime(plan['sunset_at'], usegmt=True),
            'Link': f"<{plan['doc']}>; rel=\"deprecation\"; type=\"text/html\""}


def tool_listing(plan):
    """MCP Tool definitions have no deprecation field, so the notice goes in the description and a namespaced _meta key."""
    return {'name': plan['tool'],
            'description': f"DEPRECATED: use {plan['replacement']} (same result, argument order_id). Removed after {plan['sunset_at']:%Y-%m-%d}.",
            '_meta': {'bookstore.test/deprecation': {'replacement': plan['replacement'],
                                                    'sunset': plan['sunset_at'].strftime('%Y-%m-%d')}}}


def alias(call):
    """Deterministic translation of the old argument name; anything unexpected is rejected, not guessed."""
    args = dict(call['args'])
    if set(args) != {'order_ref'}:
        return None, f"unexpected arguments {sorted(args)}"
    return {'tool': PLAN['replacement'], 'args': {'order_id': args['order_ref']}}, 'translated'


def synth_log(now):
    rows = []
    callers = [('helpdesk-agent', 'prompt-41', 30), ('helpdesk-agent', 'prompt-42', 6), ('returns-agent', 'prompt-7', 12),
               ('nightly-report (service)', None, 14)]
    for caller, prompt, n in callers:
        for i in range(n):
            rows.append({'at': now - timedelta(days=i % 14, hours=i), 'caller': caller, 'prompt_version': prompt,
                         'run': f'run-{caller[:3]}-{i}', 'tool': PLAN['tool'], 'args': {'order_ref': f'ORD-{7000 + i}'}})
    for i in range(40):
        rows.append({'at': now - timedelta(days=i % 14), 'caller': 'helpdesk-agent', 'prompt_version': 'prompt-42',
                     'run': f'run-new-{i}', 'tool': PLAN['replacement'], 'args': {'order_id': f'ORD-{8000 + i}'}})
    rows.append({'at': now - timedelta(days=2), 'caller': 'returns-agent', 'prompt_version': 'prompt-7', 'run': 'run-odd',
                 'tool': PLAN['tool'], 'args': {'order_ref': 'ORD-1', 'include': 'history'}})
    return rows


def inventory(rows, now, window_days=14):
    recent = [r for r in rows if r['tool'] == PLAN['tool'] and r['at'] > now - timedelta(days=window_days)]
    by_caller = Counter((r['caller'], r['prompt_version']) for r in recent)
    last_seen = defaultdict(lambda: None)
    for r in recent:
        k = (r['caller'], r['prompt_version'])
        last_seen[k] = max(last_seen[k], r['at']) if last_seen[k] else r['at']
    return [{'caller': c, 'prompt_version': p, 'calls': n, 'last_seen': last_seen[(c, p)].strftime('%Y-%m-%d')}
            for (c, p), n in by_caller.most_common()]


def removal_gate(inv, now, plan):
    reasons = []
    if now < plan['sunset_at']:
        reasons.append('sunset date not reached')
    if inv:
        reasons.append(f"{sum(i['calls'] for i in inv)} calls from {len(inv)} caller versions in the window")
    return {'may_remove': not reasons, 'reasons': reasons}


def main(now=datetime(2026, 12, 20, 12, tzinfo=timezone.utc)):
    rows = synth_log(now)
    inv = inventory(rows, now)
    translated = Counter(alias(r)[1] for r in rows if r['tool'] == PLAN['tool'])
    out = {'headers': headers(PLAN), 'tool_listing': tool_listing(PLAN), 'inventory': inv,
           'alias_results': dict(translated), 'removal_gate': removal_gate(inv, now, PLAN),
           'removal_gate_after_migration': removal_gate([], datetime(2027, 1, 20, tzinfo=timezone.utc), PLAN)}
    json.dump(out, sys.stdout, indent=2); print()
    return out


if __name__ == '__main__':
    main()
