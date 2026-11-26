"""Author: Sandeep Belgavi. Tests for the ZIP compressed-size agreement check."""
import io
import unittest
import zipfile
from example import build, central_entries, check_members, streaming_read, understate


class ZipSizes(unittest.TestCase):
    def test_writer_uses_a_data_descriptor(self):
        e = central_entries(build())[0]
        self.assertTrue(e["flags"] & 8)

    def test_clean_archive_agrees(self):
        data = build()
        self.assertEqual(check_members(data), [])
        self.assertEqual(len(zipfile.ZipFile(io.BytesIO(data)).read("pkg/__init__.py")), central_entries(data)[0]["usize"])

    def test_members_without_descriptor_are_not_checked(self):
        buf = io.BytesIO()                      # seekable: zipfile writes sizes into the local header
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("pkg/x.py", "VALUE = 2" + chr(10))
        data = buf.getvalue()
        self.assertFalse(central_entries(data)[0]["flags"] & 8)
        self.assertEqual(check_members(understate(data)), [])

    def test_understated_central_size_is_reported(self):
        bad = understate(build())
        self.assertEqual(check_members(bad)[0]["central"], 29)

    def test_readers_diverge_on_the_patched_archive(self):
        bad = understate(build())
        with self.assertRaises(zipfile.BadZipFile):
            zipfile.ZipFile(io.BytesIO(bad)).read("pkg/__init__.py")
        body, consumed, *_ = streaming_read(bad, central_entries(bad)[0]["lho"])
        self.assertEqual(len(body), central_entries(bad)[0]["usize"])


if __name__ == "__main__":
    unittest.main()
