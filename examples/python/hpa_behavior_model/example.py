"""Replica timeline of an autoscaling/v2 HorizontalPodAutoscaler with an explicit behavior section.
Author: Sandeep Belgavi.

Follows the Kubernetes v1.37.3 controller functions: the usage ratio and tolerance check
(replica_calculator.go), stabilizeRecommendationWithBehaviors, convertDesiredReplicasWithBehaviorRate,
calculateScaleUp/DownLimit* and getReplicasChangePerPeriod (horizontal.go). Omitted: Pod readiness,
missing metrics, CPU initialization and metric collection delay. Demand is synthetic and expressed as the
total CPU utilization of the workload in pod-percent (20 pods at 60 percent = 1200).
Standard library only. No cluster is contacted; this is a calculation, not a measurement.
"""
import json, math, sys

SYNC = 15
DEFAULT_DOWN = {'stabilizationWindowSeconds': 300, 'policies': [{'type': 'Percent', 'value': 100, 'periodSeconds': 15}], 'selectPolicy': 'Max'}
DEFAULT_UP = {'stabilizationWindowSeconds': 0, 'policies': [{'type': 'Percent', 'value': 100, 'periodSeconds': 15}, {'type': 'Pods', 'value': 4, 'periodSeconds': 15}], 'selectPolicy': 'Max'}


def raw_desired(current, demand, target, tol_up, tol_down):
    ratio = (demand / current) / target
    if (1.0 - tol_down) <= ratio <= (1.0 + tol_up):
        return current, ratio
    return math.ceil(ratio * current), ratio


def change_in_period(events, now, period):
    return sum(c for t, c in events if t > now - period)


def down_limit(current, ups, downs, rules, now):
    if rules['selectPolicy'] == 'Disabled':
        return current
    pick, result = (max, -10**9) if rules['selectPolicy'] == 'Min' else (min, 10**9)
    for p in rules['policies']:
        start = current - change_in_period(ups, now, p['periodSeconds']) + change_in_period(downs, now, p['periodSeconds'])
        proposed = start - p['value'] if p['type'] == 'Pods' else int(start * (1 - p['value'] / 100))
        result = pick(result, proposed)
    return result


def up_limit(current, ups, downs, rules, now):
    if rules['selectPolicy'] == 'Disabled':
        return current
    pick, result = (min, 10**9) if rules['selectPolicy'] == 'Min' else (max, -10**9)
    for p in rules['policies']:
        start = current - change_in_period(ups, now, p['periodSeconds']) + change_in_period(downs, now, p['periodSeconds'])
        proposed = start + p['value'] if p['type'] == 'Pods' else math.ceil(start * (1 + p['value'] / 100))
        result = pick(result, proposed)
    return result


def simulate(demand, seconds, start_replicas, target, min_r, max_r, down=None, up=None, tolerance=(0.1, 0.1), warmup=600):
    down, up = dict(DEFAULT_DOWN, **(down or {})), dict(DEFAULT_UP, **(up or {}))
    current, recs, ups, downs, rows = start_replicas, [], [], [], []
    for now in range(-warmup, seconds + 1, SYNC):
        d = demand(now)
        desired, ratio = raw_desired(current, d, target, tolerance[0], tolerance[1])
        desired = max(min_r, min(max_r, desired))
        up_rec = min([r for t, r in recs if t > now - up['stabilizationWindowSeconds']] + [desired])
        down_rec = max([r for t, r in recs if t > now - down['stabilizationWindowSeconds']] + [desired])
        rec = current
        if rec < up_rec: rec = up_rec
        if rec > down_rec: rec = down_rec
        recs.append((now, desired))
        reason = 'stable'
        new = rec
        if rec > current:
            limit = max(up_limit(current, ups, downs, up, now), current)
            if rec > min(max_r, limit):
                new, reason = min(max_r, limit), 'ScaleUpLimit'
            else:
                reason = 'scale up'
        elif rec < current:
            limit = min(down_limit(current, ups, downs, down, now), current)
            floor = max(min_r, limit)
            if rec < floor:
                new, reason = floor, 'ScaleDownLimit' if limit > min_r else 'minReplicas'
            else:
                reason = 'scale down'
        elif desired < current:
            reason = 'ScaleDownStabilized'
        elif desired > current:
            reason = 'ScaleUpStabilized'
        if new > current: ups.append((now, new - current))
        if new < current: downs.append((now, current - new))
        if now >= 0: rows.append({'t': now, 'utilization': round(d / current, 1), 'ratio': round(ratio, 3), 'raw_desired': desired,
                     'replicas_before': current, 'replicas_after': new, 'reason': reason})
        current = new
    return rows


def drop(now):
    return 1200 if now < 0 else 300  # traffic falls to a quarter at t=0


def first_time_at(rows, replicas):
    return next((r['t'] for r in rows if r['replicas_after'] <= replicas), None)


SCENARIOS = {
    'defaults': {},
    'window-60-pods-2-per-60s': {'down': {'stabilizationWindowSeconds': 60, 'policies': [{'type': 'Pods', 'value': 2, 'periodSeconds': 60}]}},
    'window-120-percent-25-per-60s': {'down': {'stabilizationWindowSeconds': 120, 'policies': [{'type': 'Percent', 'value': 25, 'periodSeconds': 60}]}},
}


def main():
    out = {}
    for name, s in SCENARIOS.items():
        rows = simulate(drop, 900, 20, 60, 2, 30, **s)
        changes = [r for r in rows if r['replicas_after'] != r['replicas_before']]
        out[name] = {'first_scale_down_s': changes[0]['t'] if changes else None, 'reaches_5_at_s': first_time_at(rows, 5),
                     'steps': [[r['t'], r['replicas_before'], r['replicas_after'], r['reason']] for r in changes]}
    tol = simulate(lambda now: 1280, 30, 20, 60, 2, 30)
    out['tolerance_64_percent_against_60'] = [[r['t'], r['utilization'], r['ratio'], r['replicas_after'], r['reason']] for r in tol]
    json.dump(out, sys.stdout, indent=2); print()
    return out


if __name__ == '__main__':
    main()
