"""Make output failures reach the exit status. Author: Sandeep Belgavi.

An agent-style command writes a JSON summary of refund cases for the fictional
Belgavi's Book Store, then a DONE marker that a scheduler polls. A full disk is
simulated with a raw stream that raises OSError(ENOSPC) once a byte budget is
spent; io.BufferedWriter sits on top exactly as with a real file, so the
failure can surface at write(), flush() or close().

Writers:
- swallow: catches every error, writes the marker, exits 0.
- marker_first: writes the marker before closing the output; the close fails later.
- checked: writes to a temporary name, flushes, closes, renames, then writes
  the marker; any OSError goes to stderr with exit status 1 and no marker.

Run as a child process so the exit status is real: python report_writer.py <mode> <dir> <budget>
"""
import errno
import io
import json
import os
import sys
from pathlib import Path

CASES = [{'case': f'CASE-{8100 + i}', 'customer': n, 'refund_paise': 39_900 + i * 1_000}
         for i, n in enumerate(['Geetha', 'Jenya', 'Tanishka', 'Dinky', 'Hansini'] * 40)]


class FullDisk(io.RawIOBase):
    """A raw file that accepts `budget` bytes, then fails like ENOSPC."""

    def __init__(self, path, budget):
        self.f = open(path, 'wb', buffering=0)
        self.budget = budget

    def writable(self):
        return True

    def write(self, b):
        if self.budget <= 0:
            raise OSError(errno.ENOSPC, 'No space left on device (simulated)')
        n = min(len(b), self.budget)
        self.f.write(bytes(b[:n]))
        self.budget -= n
        return n

    def close(self):
        if not self.closed:
            self.f.close()
        super().close()


def open_output(path, budget):
    return io.TextIOWrapper(io.BufferedWriter(FullDisk(path, budget), buffer_size=8192), encoding='utf-8')


def payload():
    return json.dumps({'author': 'Sandeep Belgavi', 'synthetic': True, 'cases': CASES}, indent=1)


def swallow(out_dir, budget):
    try:
        f = open_output(out_dir / 'summary.json', budget)
        f.write(payload())
        f.close()
    except Exception:
        pass
    (out_dir / 'DONE').write_text('ok\n')
    return 0


def marker_first(out_dir, budget):
    f = open_output(out_dir / 'summary.json', budget)
    f.write(payload())          # fits in the buffer or fails partway; either way not yet durable
    (out_dir / 'DONE').write_text('ok\n')
    f.close()                   # the remaining buffered bytes fail here, after the marker
    return 0


def checked(out_dir, budget):
    tmp = out_dir / 'summary.json.tmp'
    try:
        f = open_output(tmp, budget)
        try:
            f.write(payload())
            f.flush()
        finally:
            f.close()
        os.replace(tmp, out_dir / 'summary.json')
    except OSError as e:
        tmp.unlink(missing_ok=True)
        print(f'error: summary not written: {e}', file=sys.stderr)
        return 1
    (out_dir / 'DONE').write_text('ok\n')
    return 0


MODES = {'swallow': swallow, 'marker_first': marker_first, 'checked': checked}


def main():
    mode, out_dir, budget = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
    out_dir.mkdir(parents=True, exist_ok=True)
    sys.exit(MODES[mode](out_dir, budget))


if __name__ == '__main__':
    main()
