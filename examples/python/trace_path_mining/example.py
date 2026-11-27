"""Mine tool-call variants from recorded agent runs. Author: Sandeep Belgavi.

Synthetic help-desk runs for the fictional Belgavi's Book Store. Each run records case attributes and
the execute_tool spans (gen_ai.tool.name) in start order. The script normalizes retries, counts variants,
checks whether case attributes already determine the variant, and replays a compiled workflow.
Standard library only. No model is called.
"""
from collections import Counter, defaultdict
import json, random, sys

TOOLS_BY_RULE = {
    'return_in_window': ('get_order', 'check_return_window', 'create_return_label'),
    'return_late': ('get_order', 'check_return_window', 'escalate_to_person'),
    'refund_status': ('get_order', 'get_refund'),
    'damaged_small': ('get_order', 'request_photo', 'create_replacement'),
    'damaged_large': ('get_order', 'request_photo', 'request_approval', 'create_replacement'),
}
FREE_FORM = ['search_help_articles', 'get_order', 'get_customer', 'escalate_to_person', 'send_reply']


def synth_runs(n=400, seed=1127):
    """Deterministic synthetic traces; 'other' cases have genuinely varied paths."""
    rnd = random.Random(seed)
    runs = []
    for i in range(n):
        kind = rnd.choices(['return', 'refund_status', 'damaged', 'other'], [40, 25, 20, 15])[0]
        days = rnd.randint(1, 60)
        total = rnd.choice([350, 600, 900, 1500, 2400, 3200])
        if kind == 'return':
            path = list(TOOLS_BY_RULE['return_in_window' if days <= 30 else 'return_late'])
        elif kind == 'refund_status':
            path = list(TOOLS_BY_RULE['refund_status'])
        elif kind == 'damaged':
            path = list(TOOLS_BY_RULE['damaged_large' if total > 2000 else 'damaged_small'])
        else:
            path = rnd.sample(FREE_FORM, rnd.randint(2, 4))
        if rnd.random() < 0.06:  # a retried tool call shows up as an immediate repeat
            j = rnd.randrange(len(path)); path.insert(j, path[j])
        if kind != 'other' and rnd.random() < 0.03:  # a run that went somewhere unusual
            path.append('search_help_articles')
        runs.append({'case': f'CASE-{5000 + i}', 'kind': kind, 'days_since_delivery': days,
                     'order_total': total, 'tools': path})
    return runs


def normalize(tools):
    """Collapse immediate repeats (retries of the same tool) so they do not split variants."""
    out = []
    for t in tools:
        if not out or out[-1] != t:
            out.append(t)
    return tuple(out)


ATTRS = {'within_30_days': lambda r: r['days_since_delivery'] <= 30, 'over_2000': lambda r: r['order_total'] > 2000}
SUBSETS = [(), ('within_30_days',), ('over_2000',), ('within_30_days', 'over_2000')]


def key_of(run, attrs):
    return tuple(ATTRS[a](run) for a in attrs)


def mine(runs, min_share=0.05, min_purity=0.9):
    """Per case kind, find the smallest attribute set whose groups each have one dominant variant."""
    raw = Counter(tuple(r['tools']) for r in runs)
    norm = Counter(normalize(r['tools']) for r in runs)
    by_kind = defaultdict(list)
    for r in runs:
        by_kind[r['kind']].append(r)
    compiled, rows = {}, []
    for kind, members in sorted(by_kind.items(), key=lambda kv: -len(kv[1])):
        chosen = None
        for attrs in SUBSETS:
            groups = defaultdict(Counter)
            for r in members:
                groups[key_of(r, attrs)][normalize(r['tools'])] += 1
            if all(g.most_common(1)[0][1] / sum(g.values()) >= min_purity for g in groups.values()):
                chosen = (attrs, groups); break
        if chosen is None:
            rows.append({'kind': kind, 'runs': len(members), 'decided_by': None, 'compiled': False,
                         'distinct_variants': len({normalize(r['tools']) for r in members})})
            continue
        attrs, groups = chosen
        for k, g in sorted(groups.items()):
            top, count = g.most_common(1)[0]; total = sum(g.values())
            keep = total / len(runs) >= min_share
            if keep:
                compiled[(kind, attrs, k)] = top
            rows.append({'kind': kind, 'decided_by': list(attrs), 'values': list(k), 'runs': total,
                         'top_variant': ' > '.join(top), 'purity': round(count / total, 3), 'compiled': keep})
    return raw, norm, compiled, rows


def route(run, compiled):
    for (kind, attrs, k), path in compiled.items():
        if run['kind'] == kind and key_of(run, attrs) == k:
            return path
    return None


def replay(runs, compiled):
    """A compiled workflow either owns the case (and must match the recorded path) or hands it to the agent."""
    owned = matched = 0
    for r in runs:
        path = route(r, compiled)
        if path is None:
            continue
        owned += 1
        matched += normalize(r['tools']) == path
    return owned, matched


def main():
    runs = synth_runs()
    raw, norm, compiled, rows = mine(runs)
    owned, matched = replay(runs, compiled)
    top4 = sum(c for _, c in norm.most_common(4))
    report = {
        'runs': len(runs), 'raw_variants': len(raw), 'normalized_variants': len(norm),
        'top4_variant_share': round(top4 / len(runs), 3),
        'compiled_feature_groups': len(compiled), 'owned_by_workflow': owned,
        'owned_share': round(owned / len(runs), 3), 'workflow_matches_recorded_path': matched,
        'match_rate_on_owned': round(matched / owned, 3) if owned else None,
        'residual_to_agent': len(runs) - owned, 'groups': rows,
    }
    json.dump(report, sys.stdout, indent=2); print()
    return report


if __name__ == '__main__':
    main()
