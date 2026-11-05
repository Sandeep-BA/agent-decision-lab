"""Compare per-trace and per-run sampling on 2,000 synthetic agent runs. Author: Sandeep Belgavi."""
from sampling import sample, synthetic_runs, threshold, tracestate_for_run

if __name__ == '__main__':
    runs = synthetic_runs(2000)
    multi = sum(1 for _, t in runs if t > 1)
    print('runs %d, traces %d, runs with more than one trace %d' % (len(runs), sum(t for _, t in runs), multi))
    print('threshold for p=0.1: %014x' % threshold(0.1))
    print('tracestate for run-00042: %s' % tracestate_for_run('run-00042'))
    for p in (0.1, 0.25):
        for policy in ('trace', 'run'):
            r = sample(runs, p, policy)
            print('p=%.2f %-5s kept whole %4d  partial %4d  dropped %4d  traces kept %4d of %d' % (
                p, policy, r['kept_whole'], r['partial'], r['dropped'], r['traces_kept'], r['traces']))
