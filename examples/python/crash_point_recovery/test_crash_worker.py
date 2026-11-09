"""Independent oracle over the durable stores. Author: Sandeep Belgavi."""
import sqlite3, subprocess, sys, unittest, uuid
from contextlib import closing, contextmanager
from pathlib import Path
from crash_worker import POINTS, run

HERE = Path(__file__).resolve().parent


@contextmanager
def fixture_database():
    database = HERE / ('test-fixture-' + uuid.uuid4().hex + '.db')
    try:
        yield database
    finally:
        for suffix in ('', '-journal', '-wal', '-shm'):
            file = Path(str(database) + suffix)
            if file.exists():
                file.unlink()


def crash(database, point, *extra):
    return subprocess.run([sys.executable, str(HERE / 'crash_worker.py'), str(database), point, *extra], capture_output=True, timeout=30)


class CrashMatrix(unittest.TestCase):
    def test_each_boundary_keeps_one_effect(self):
        for point in POINTS:
            with self.subTest(point=point), fixture_database() as database:
                self.assertEqual(crash(database, point).returncode, 17)
                run(database)
                run(database)
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM effect').fetchone()[0], 1)
                    self.assertEqual(db.execute('SELECT value FROM effect').fetchone()[0], 'SYNTHETIC REFUND NOTE')
                    self.assertEqual(db.execute('SELECT done FROM task').fetchone()[0], 1)

    def test_unsafe_retry_duplicates_the_effect(self):
        with fixture_database() as database:
            self.assertEqual(crash(database, 'after_effect', 'unsafe').returncode, 17)
            run(database, unsafe=True)
            with closing(sqlite3.connect(database)) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM effect').fetchone()[0], 2)

    def test_conflicting_payload_is_rejected(self):
        with fixture_database() as database:
            run(database)
            with closing(sqlite3.connect(database)) as db, db:
                db.execute("UPDATE task SET payload='changed'")
            with self.assertRaises(ValueError):
                run(database)


if __name__ == '__main__':
    unittest.main()
