"""Tests for the rootless mapping arithmetic. Author: Sandeep Belgavi."""
import unittest
from uid_mapping import SUBUID, container_map, parse_subuid, to_container, to_host

R = parse_subuid(SUBUID, "jenya")


class MappingTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(R, [(100000, 65536)])
        self.assertEqual(parse_subuid(SUBUID, "dinky"), [])

    def test_default_container_root_is_the_user(self):
        self.assertEqual(to_host(0, "host", 1000, R), 1000)

    def test_default_container_uid_1000_is_100999(self):
        self.assertEqual(to_host(1000, "host", 1000, R), 100999)

    def test_default_user_file_looks_root_owned(self):
        self.assertEqual(to_container(1000, "host", 1000, R), 0)

    def test_keep_id_maps_uid_to_itself(self):
        self.assertEqual(to_host(1000, "keep-id", 1000, R), 1000)
        self.assertEqual(to_container(1000, "keep-id", 1000, R), 1000)

    def test_keep_id_root_is_a_subordinate_id(self):
        self.assertEqual(to_host(0, "keep-id", 1000, R), 100000)

    def test_keep_id_segments(self):
        self.assertEqual(container_map("keep-id", 1000, R), [(0, 1, 1000), (1000, 0, 1), (1001, 1001, 64536)])

    def test_keep_id_custom_uid(self):
        self.assertEqual(to_host(200, "keep-id", 1000, R, keep_uid=200), 1000)

    def test_unmapped_ids(self):
        self.assertIsNone(to_host(70000, "host", 1000, R))
        self.assertIsNone(to_container(4242, "host", 1000, R))
        self.assertIsNone(to_container(1000, "nomap", 1000, R))


if __name__ == "__main__":
    unittest.main()
