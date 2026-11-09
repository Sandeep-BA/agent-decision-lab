"""Author: Sandeep Belgavi."""
import sqlite3, unittest
from safe_sort import list_books

BOOKS = [(1, 'Zebra Tales', 310, 3), (2, 'Atlas of Rivers', 310, 1), (3, 'Birdsong', 120, 2)]


class Sort(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.execute('CREATE TABLE book(id INTEGER PRIMARY KEY,title TEXT,page_count INTEGER,published_on INTEGER)')
        self.db.executemany('INSERT INTO book VALUES(?,?,?,?)', BOOKS)

    def test_exact_order_and_ties(self):
        expected = {('pages', 'asc'): [3, 1, 2], ('pages', 'desc'): [1, 2, 3], ('title', 'asc'): [2, 3, 1],
                    ('title', 'desc'): [1, 3, 2], ('published', 'asc'): [2, 3, 1], ('published', 'desc'): [1, 3, 2]}
        for (key, direction), ids in expected.items():
            with self.subTest(key=key, direction=direction):
                self.assertEqual([r[0] for r in list_books(self.db, key, direction)], ids)

    def test_bound_minimum(self):
        self.assertEqual([r[0] for r in list_books(self.db, 'pages', 'asc', 2)], [3, 2])

    def test_rejected_before_the_database(self):
        class NoCall:
            def execute(self, *args):
                raise AssertionError('database must not be called')
        for key, direction in [('pages; select 1', 'asc'), ('title', 'desc nulls first'), ('unknown', 'asc'), (' title', 'asc')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                list_books(NoCall(), key, direction)


if __name__ == '__main__':
    unittest.main()
