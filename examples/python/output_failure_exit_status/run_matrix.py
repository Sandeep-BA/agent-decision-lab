"""Run every writer as a real child process and record what a scheduler would see. Author: Sandeep Belgavi."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIG = 10_000_000
sys.path.insert(0, str(HERE))
from report_writer import payload  # noqa: E402
SIZE = len(payload().encode('utf-8'))


def run(mode, budget):
    with tempfile.TemporaryDirectory() as d:
        p = subprocess.run([sys.executable, str(HERE / 'report_writer.py'), mode, d, str(budget)],
                           capture_output=True, text=True)
        out = Path(d) / 'summary.json'
        try:
            json.loads(out.read_text(encoding='utf-8'))
            valid = True
        except (OSError, ValueError):
            valid = False
        last = (p.stderr.strip().splitlines() or [''])[-1]
        return {'mode': mode, 'budget': budget, 'exit': p.returncode, 'marker': (Path(d) / 'DONE').exists(),
                'summary_valid': valid, 'stderr_last': last[:90]}


def stdout_flush_at_exit():
    """A child whose buffered stdout cannot be flushed when the interpreter exits."""
    child = 'import sys, time\nsys.stdout.write("x" * 100)\ntime.sleep(0.5)\n'
    p = subprocess.Popen([sys.executable, '-c', child], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.stdout.close()
    err = p.stderr.read().decode(errors='replace').strip().splitlines()
    return {'exit': p.wait(), 'stderr_last': err[-1] if err else ''}


def matrix():
    rows = []
    for mode in ('swallow', 'marker_first', 'checked'):
        for budget in (BIG, 4096, SIZE - 100):
            rows.append(run(mode, budget))
    return rows


def main():
    print('payload bytes:', SIZE)
    for r in matrix():
        print(r)
    print('stdout flushed at exit:', stdout_flush_at_exit())


if __name__ == '__main__':
    main()
