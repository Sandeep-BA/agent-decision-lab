"""Author: Sandeep Belgavi. Expected outcomes for the shared-connection lease model."""
import unittest
from leases import scenario


class LeaseTests(unittest.TestCase):
    def test_without_leases_state_bleeds_between_chats(self):
        server, _ = scenario(supports_leases=False)
        self.assertEqual(server.notes[0], ("CASE-4415", "customer sent the return label"))

    def test_leases_isolate_selected_case(self):
        server, _ = scenario()
        self.assertEqual(server.notes[:2], [("CASE-4410", "customer sent the return label"), ("CASE-4415", "asked for a replacement copy")])

    def test_caller_supplied_lease_is_overridden(self):
        spoofed, _ = scenario(spoof=True, override_meta=False)
        self.assertEqual(spoofed.notes[1][0], "CASE-4410")
        guarded, _ = scenario(spoof=True)
        self.assertEqual(guarded.notes[1][0], "CASE-4415")

    def test_cancel_before_release_stops_late_write(self):
        server, host = scenario()
        self.assertNotIn(("CASE-4410", "refund approved"), server.notes)
        self.assertEqual(host.dropped, [])

    def test_release_without_cancel_writes_after_close(self):
        server, host = scenario(cancel_before_release=False)
        self.assertIn(("CASE-4410", "refund approved"), server.notes)
        self.assertEqual(host.dropped, [5])

    def test_request_ids_unique_on_the_connection(self):
        _, host = scenario()
        ids = [int(l.split("id=")[1].split()[0]) for l in host.log if "tools/call" in l]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
