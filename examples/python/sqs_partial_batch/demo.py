"""Compare whole-batch failure with partial batch responses on the fixture. Author: Sandeep Belgavi."""
import json, pathlib
from queue_sim import run

data = json.loads((pathlib.Path(__file__).resolve().parent / 'fixtures.json').read_text(encoding='utf-8'))
for mode in ('raise', 'partial', 'partial_bad_id'):
    r = run(data['messages'], mode, transient_failures=data['transient_failures'])
    print('%-15s invocations=%d deliveries=%d redeliveries=%d dead_lettered=%s applied=%d' % (
        mode, r['invocations'], r['deliveries'], r['redeliveries'], ','.join(r['dead_lettered']) or '-', r['applied']))
