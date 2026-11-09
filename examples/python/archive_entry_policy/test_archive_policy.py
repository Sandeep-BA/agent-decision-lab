"""Author: Sandeep Belgavi."""
import unittest
from archive_policy import validate_entries


class Policy(unittest.TestCase):
    def test_accepts_plain_tree(self):
        self.assertEqual(validate_entries([('rootfs/', 'directory'), ('rootfs/a', 'file')]), {'rootfs', 'rootfs/a'})

    def test_negative_corpus(self):
        for rows in ([('rootfs/', 'directory'), ('rootfs', 'symlink')], [('/root', 'file')], [('../escape', 'file')],
                     [('a', 'device')], [('./a', 'file'), ('a', 'file')]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                validate_entries(rows)


if __name__ == '__main__':
    unittest.main()
